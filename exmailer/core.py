"""Core ExchangeEmailer class with flexible template system."""

import logging
import ssl
from collections.abc import Sequence
from typing import Any, Literal, Optional, Union

from exchangelib import (
    DELEGATE,
    Account,
    Build,
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
            emailer = ExchangeEmailer(config={
                "domain": "corp",
                "username": "john.doe",
                "password": "secret123",
                "server": "mail.corp.com",
                "email_domain": "corp.com"
            })

            # Method 2: Config file
            emailer = ExchangeEmailer(config_path="~/.config/exmailer/config.json")

            # Method 3: Auto-discovery (looks in default locations)
            emailer = ExchangeEmailer()
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
            logger.warning(f"⚠️ SSL configuration failed: {str(e)}")
            return ssl._create_unverified_context()

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
            raise AuthenticationError(f"Authentication failed: {str(e)}") from e
        except TransportError as e:
            raise ExchangeEmailConnectionError(f"Connection failed: {str(e)}") from e
        except Exception as e:  # pragma: no cover
            raise ExchangeEmailConnectionError(f"Unexpected connection error: {str(e)}") from e

    def send_email(
        self,
        subject: str,
        body: str,
        recipients: Sequence[str],
        attachments: Sequence[str] | None = None,
        cc_recipients: Sequence[str] | None = None,
        bcc_recipients: Sequence[str] | None = None,
        template: Optional[Union[str, TemplateType]] = TemplateType.PERSIAN,
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
            template_vars = template_vars or {}
            template_vars["body"] = body.format(**template_vars)

            if template is None or template == TemplateType.PLAIN:
                # No template - use body as-is
                formatted_body = body.format(**template_vars)
            else:
                # Get template (handles both TemplateType enum and string names)
                template_html = get_template(template)

                # Format body with template
                formatted_body = template_html.format(**template_vars)

            # Create message
            msg = Message(
                account=self.account,
                subject=subject,
                body=HTMLBody(formatted_body),
                to_recipients=[Mailbox(email_address=email) for email in recipients],
                cc_recipients=cc_recipients or [],
                bcc_recipients=bcc_recipients or [],
                importance=importance,
            )

            # Add CC/BCC recipients if provided
            if cc_recipients:
                msg.cc_recipients = [Mailbox(email_address=email) for email in cc_recipients]
            if bcc_recipients:
                msg.bcc_recipients = [Mailbox(email_address=email) for email in bcc_recipients]

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
                        logger.error(f"Failed to attach {attachment['path']}: {str(e)}")
                        if self.verbose:
                            print(f"⚠️ Failed to attach {attachment['path']}: {str(e)}")

            # Send email
            save_copy = self.config.get("save_copy", True)
            try:
                msg.send(save_copy=save_copy)
            except Exception as e:
                raise SendError(f"Failed to send email: {str(e)}") from e  # ← Wrap exception

            logger.info(f"✅ Email sent successfully to {', '.join(recipients)}")
            if self.verbose:  # pragma: no cover
                print(f"✅ Email sent successfully to {', '.join(recipients)}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")
            if self.verbose:  # pragma: no cover
                print(f"❌ Failed to send email: {str(e)}")
            raise

    def __enter__(self):  # pragma: no cover
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # pragma: no cover
        # Cleanup resources if needed
        pass
