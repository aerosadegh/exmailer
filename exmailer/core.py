"""Core ExchangeEmailer class with flexible template system."""

import datetime
import logging
import ssl
from collections.abc import Sequence
from typing import Any, Literal
from zoneinfo import ZoneInfo

from exchangelib import (
    DELEGATE,
    Account,
    Build,
    CalendarItem,
    Configuration,
    Credentials,
    FileAttachment,
    HTMLBody,
    Mailbox,
    Message,
    Version,
)
from exchangelib.errors import TransportError, UnauthorizedError
from exchangelib.protocol import BaseProtocol
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

from .config import load_config
from .exceptions import (
    AuthenticationError,
    ExchangeEmailConnectionError,
    SendError,
)
from .templates import TemplateType, get_template
from .utils import validate_attachments

logger = logging.getLogger(__name__)


class SecureHTTPAdapter(HTTPAdapter):
    """
    Custom HTTP Adapter that injects a secure SSL context.
    Compatible with exchangelib which instantiates adapters without args.
    """

    def __init__(self, ssl_context: ssl.SSLContext | None = None, **kwargs):
        if ssl_context is None:  # pragma: no cover
            ssl_context = ssl.create_default_context()
            ssl_context.load_default_certs()

        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context,
            **pool_kwargs,
        )


class ExchangeEmailer:
    """Send emails via Microsoft Exchange server with flexible HTML template support."""

    def __init__(
        self,
        config_path: str | None = None,
        config: dict[str, Any] | None = None,  # NEW parameter
        verbose: bool = False,
    ):
        """
        Initialize the Exchange emailer.

        Args:
            config_path: Path to JSON/YAML configuration file
            config: Direct configuration dictionary (highest priority)
            verbose: Enable verbose logging

        Examples:
            # Method 1: Programmatic config (recommended for scripts)
            ```python
            emailer = ExchangeEmailer(config={
                "domain": "corp",
                "username": "john.doe",
                "password": "secret123",
                "server": "mail.corp.com",
                "email_domain": "corp.com"
            })
            ```

            # Method 2: Config file
            ```python
            emailer = ExchangeEmailer(config_path="~/.config/exmailer/config.json")
            ```

            # Method 3: Auto-discovery (looks in default locations)
            ```python
            emailer = ExchangeEmailer()
            ```
        """
        self.verbose = verbose
        self.config = load_config(config_path=config_path, config_dict=config)
        self._patch_exchangelib_adapter()

        if verbose:  # pragma: no cover
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s %(levelname)s %(message)s",
                filename="exchange_debug.log",
            )

        self.account = self._connect_to_exchange()

    def _patch_exchangelib_adapter(self):
        """
        Configure exchangelib to use our SecureHTTPAdapter.
        This ensures all connections use system SSL certificates.
        """
        if BaseProtocol.HTTP_ADAPTER_CLS != SecureHTTPAdapter:
            BaseProtocol.HTTP_ADAPTER_CLS = SecureHTTPAdapter
            logger.debug("🔒 Patched exchangelib with SecureHTTPAdapter")

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create a secure SSL context using standard libraries."""
        try:
            ctx = ssl.create_default_context()
            ctx.load_default_certs()
            logger.info("✅ SSL configured with system certificates")
            return ctx
        except Exception as e:  # pragma: no cover
            logger.warning(f"⚠️ SSL configuration failed: {e!s}")
            # noqa S323 - intentional fallback for connectivity resilience
            return ssl._create_unverified_context()  # noqa: S323

    def _connect_to_exchange(self):
        """Connect to Exchange server with provided credentials."""
        try:
            full_username = f"{self.config['domain']}\\{self.config['username']}"
            credentials = Credentials(username=full_username, password=self.config["password"])
            version = Version(build=Build(15, 1, 2248, 0))

            email_domain = self.config.get("email_domain")
            if email_domain is None:  # pragma: no cover
                raise ValueError("`email_domain` must be configured!")
            primary_email = f"{self.config['username']}@{email_domain}"

            config = Configuration(
                service_endpoint=f"https://{self.config['server']}/EWS/Exchange.asmx",
                credentials=credentials,
                auth_type=self.config["auth_type"],
                version=version,
            )

            account = Account(
                primary_smtp_address=primary_email,
                config=config,
                autodiscover=False,
                access_type=DELEGATE,
            )

            # Inject Secure Adapter directly into this account's session
            if account.protocol:
                ssl_context = self._create_ssl_context()
                adapter = SecureHTTPAdapter(ssl_context=ssl_context)

                session = account.protocol.get_session()
                session.mount("https://", adapter)
                account.protocol.release_session(session)

            if self.verbose:  # pragma: no cover
                print("✅ Connected to Exchange Server")
            logger.info("Successfully connected to Exchange Server")
            return account

        except UnauthorizedError as e:
            raise AuthenticationError(f"Authentication failed: {e!s}") from e
        except TransportError as e:
            raise ExchangeEmailConnectionError(f"Connection failed: {e!s}") from e
        except Exception as e:  # pragma: no cover
            raise ExchangeEmailConnectionError(f"Unexpected connection error: {e!s}") from e

    def _render_body(
        self, body: str, template: str | TemplateType | None, template_vars: dict[str, Any] | None
    ) -> str:
        """Helper method to share template rendering between Emails and Calendar Invites."""
        template_vars = template_vars or {}
        template_vars["body"] = body.format(**template_vars)

        if template is None or template == TemplateType.PLAIN:
            return body.format(**template_vars)

        template_html = get_template(template)
        return template_html.format(**template_vars)

    def _ensure_timezone(self, dt: datetime.datetime) -> datetime.datetime:
        """Ensure the datetime is timezone aware to prevent Exchange Server rejection."""
        if dt.tzinfo is None:
            # Fallback to local timezone or UTC if user passes a naive datetime
            fallback_tz = self.config.get("timezone", "UTC")
            return dt.replace(tzinfo=ZoneInfo(fallback_tz))
        return dt

    def send_email(
        self,
        subject: str,
        body: str,
        recipients: Sequence[str],
        attachments: Sequence[str] | None = None,
        cc_recipients: Sequence[str] | None = None,
        bcc_recipients: Sequence[str] | None = None,
        template: str | TemplateType | None = TemplateType.PERSIAN,
        template_vars: dict[str, Any] | None = None,
        importance: Literal["Low", "Normal", "High"] = "Normal",
    ) -> bool:
        """
        Send an email with optional attachments.

        Args:
            subject: Email subject
            body: Email body content
            recipients: List of recipient email addresses
            attachments: List of file paths to attach
            cc_recipients: List of CC recipient email addresses
            bcc_recipients: List of BCC recipient email addresses
            template: Template to use. Options:
                - TemplateType.PERSIAN: Persian RTL template
                - TemplateType.DEFAULT: English LTR template
                - TemplateType.PLAIN: Plain text (no template)
                - str: Custom template name registered via register_custom_template()
                - None: Use plain text (no template)
            template_vars: Variables to replace in template (e.g., {"date": "14/08/1404"})

        Returns:
            True if email was sent successfully

        Examples:
            >>> # Using built-in Persian template
            >>> emailer.send_email(
            ...     subject="سلام",
            ...     body="متن پیام",
            ...     recipients=["user@example.com"],
            ...     template=TemplateType.PERSIAN
            ... )

            >>> # Using built-in English template
            >>> emailer.send_email(
            ...     subject="Hello",
            ...     body="Message content",
            ...     recipients=["user@example.com"],
            ...     template=TemplateType.DEFAULT
            ... )

            >>> # Using plain text (no template)
            >>> emailer.send_email(
            ...     subject="Hello",
            ...     body="Plain message",
            ...     recipients=["user@example.com"],
            ...     template=None
            ... )

            >>> # Using custom template
            >>> emailer.send_email(
            ...     subject="Newsletter",
            ...     body="Content here",
            ...     recipients=["user@example.com"],
            ...     template="my_custom_template"
            ... )
        """
        try:
            # Get the appropriate template
            ## Apply template variables if provided
            formatted_body = self._render_body(body, template, template_vars)

            # Create message
            msg = Message(
                account=self.account,
                subject=subject,
                body=HTMLBody(formatted_body),
                to_recipients=[Mailbox(email_address=email) for email in recipients],
                cc_recipients=(
                    [Mailbox(email_address=e) for e in cc_recipients] if cc_recipients else []
                ),
                bcc_recipients=(
                    [Mailbox(email_address=e) for e in bcc_recipients] if bcc_recipients else []
                ),
                importance=importance,
            )

            # Process attachments
            if attachments:
                validated_attachments = validate_attachments(attachments)
                for attachment in validated_attachments:
                    try:
                        with open(attachment["path"], "rb") as f:
                            content = f.read()

                        file_attachment = FileAttachment(
                            name=attachment["name"],
                            content=content,
                            content_type=attachment["content_type"],
                        )
                        msg.attach(file_attachment)
                        logger.info(
                            f"Attached: {attachment['name']} ({attachment['size'] // 1024} KB)"
                        )

                    except Exception as e:  # pragma: no cover
                        logger.error(f"Failed to attach {attachment['path']}: {e!s}")
                        if self.verbose:
                            print(f"⚠️ Failed to attach {attachment['path']}: {e!s}")

            # Send email
            save_copy = self.config.get("save_copy", True)
            try:
                msg.send(save_copy=save_copy)
            except Exception as e:
                raise SendError(f"Failed to send email: {e!s}") from e  # ← Wrap exception

            logger.info(f"✅ Email sent successfully to {', '.join(recipients)}")
            if self.verbose:  # pragma: no cover
                print(f"✅ Email sent successfully to {', '.join(recipients)}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email: {e!s}")
            if self.verbose:  # pragma: no cover
                print(f"❌ Failed to send email: {e!s}")
            raise

    # ==========================================
    # CALENDAR / MEETING METHODS
    # ==========================================

    def send_meeting_invite(
        self,
        subject: str,
        start: datetime.datetime,
        end: datetime.datetime,
        body: str = "",
        required_attendees: Sequence[str] | None = None,
        optional_attendees: Sequence[str] | None = None,
        location: str = "",
        template: str | TemplateType | None = TemplateType.PERSIAN,
        template_vars: dict[str, Any] | None = None,
        is_response_requested: bool = True,
    ) -> str:
        """
        Creates a new meeting in the Exchange calendar and sends invites.

        Args:
            subject: The subject or title of the meeting.
            start: A timezone-aware datetime object for the meeting start.
            end: A timezone-aware datetime object for the meeting end.
            body: The HTML or plain text body of the meeting invite.
            required_attendees: Sequence of email addresses for required participants.
            optional_attendees: Sequence of email addresses for optional participants.
            location: The physical or virtual location of the meeting.
            template: The template to wrap the body in (default: Persian RTL).
            template_vars: Variables for dynamic injection into the template.
            is_response_requested: If True, asks attendees to RSVP (Accept/Decline).

        Returns:
            str: The unique Exchange ID of the created meeting item.

        Raises:
            SendError: If the meeting creation or network request fails.
        """
        try:
            formatted_body = self._render_body(body, template, template_vars)

            # Ensure timezones are attached before sending to EWS
            start_dt = self._ensure_timezone(start)
            end_dt = self._ensure_timezone(end)

            item = CalendarItem(
                account=self.account,
                folder=self.account.calendar,
                start=start_dt,
                end=end_dt,
                subject=subject,
                body=HTMLBody(formatted_body),
                location=location,
                required_attendees=required_attendees or [],
                optional_attendees=optional_attendees or [],
                is_response_requested=is_response_requested,
            )

            item.save(send_meeting_invitations="SendToAllAndSaveCopy")
            logger.info(f"✅ Meeting '{subject}' created successfully.")
            return item.id  # type: ignore

        except Exception as e:
            logger.error(f"❌ Failed to create meeting invite: {e!s}")
            raise SendError(f"Failed to create meeting: {e!s}") from e

    def update_meeting_invite(
        self,
        exchange_id: str,
        subject: str,
        start: datetime.datetime,
        end: datetime.datetime,
        body: str = "",
        required_attendees: Sequence[str] | None = None,
        optional_attendees: Sequence[str] | None = None,
        location: str = "",
        template: str | TemplateType | None = TemplateType.PERSIAN,
        template_vars: dict[str, Any] | None = None,
        is_response_requested: bool = True,
    ) -> bool:
        """
        Updates an existing meeting by its Exchange ID and notifies attendees.

        Args:
            exchange_id: The unique ID returned when the meeting was created.
            subject: The updated subject of the meeting.
            start: The updated timezone-aware start time.
            end: The updated timezone-aware end time.
            body: The updated body content.
            required_attendees: Updated sequence of required attendees.
            optional_attendees: Updated sequence of optional attendees.
            location: The updated meeting location.
            template: The template to use for the updated body.
            template_vars: Variables for dynamic injection into the template.
            is_response_requested: If True, asks attendees to RSVP to the update.

        Returns:
            bool: True if the meeting was updated successfully, False if ID is missing.

        Raises:
            SendError: If the meeting update request fails.
        """
        if not exchange_id:
            logger.warning("Update aborted: `exchange_id` is empty or None.")
            return False

        try:
            item = self.account.calendar.get(id=exchange_id)
            formatted_body = self._render_body(body, template, template_vars)

            item.start = self._ensure_timezone(start)
            item.end = self._ensure_timezone(end)
            item.subject = subject
            item.body = HTMLBody(formatted_body)
            item.location = location
            item.required_attendees = required_attendees or []
            item.optional_attendees = optional_attendees or []
            item.is_response_requested = is_response_requested

            item.save(send_meeting_invitations="SendToAllAndSaveCopy")
            logger.info(f"✅ Meeting '{subject}' updated successfully.")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to update meeting {exchange_id}: {e!s}")
            raise SendError(f"Failed to update meeting: {e!s}") from e

    def cancel_meeting_invite(self, exchange_id: str) -> bool:
        """
        Cancels an existing meeting by its Exchange ID and notifies attendees.

        Args:
            exchange_id: The unique ID returned when the meeting was created.

        Returns:
            bool: True if the meeting was canceled successfully, False if `exchange_id` is empty or None.

        Raises:
            SendError: If the meeting cancellation request fails.
        """
        if not exchange_id:
            logger.warning("Cancellation aborted: `exchange_id` is empty or None.")
            return False

        try:
            item = self.account.calendar.get(id=exchange_id)
            item.delete(send_meeting_cancellations="SendToAllAndSaveCopy")
            logger.info(f"✅ Meeting {exchange_id} canceled successfully.")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to cancel meeting {exchange_id}: {e!s}")
            raise SendError(f"Failed to cancel meeting: {e!s}") from e

    def __enter__(self):  # pragma: no cover
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # pragma: no cover
        # Cleanup resources if needed
        pass
