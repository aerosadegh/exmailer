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
from urllib3.util.ssl_ import create_urllib3_context

from .config import load_config
from .exceptions import (
    AuthenticationError,
    ExchangeEmailConnectionError,
    SendError,
)
from .templates import TemplateType, get_template, register_custom_template
from .utils import validate_attachments

logger = logging.getLogger(__name__)


class SecureHTTPAdapter(HTTPAdapter):
    """
    Custom HTTP Adapter that allows injecting a specific SSL context.
    This ensures we use system certs without patching exchangelib globally.
    """

    def __init__(self, ssl_context: ssl.SSLContext, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        # Inject the custom SSL context into the pool manager
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context,
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
        # Load config with layered priority
        self.config = load_config(config_path=config_path, config_dict=config)

        # Setup logging
        if verbose:
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s %(levelname)s %(message)s",
                filename="exchange_debug.log",
            )

        # Configure SSL context
        # self._configure_ssl()

        # Connect to Exchange server
        self.account = self._connect_to_exchange()

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create a secure SSL context using standard libraries."""
        try:
            ctx = ssl.create_default_context()
            ctx.load_default_certs()
            logger.info("✅ SSL configured with system certificates")
            return ctx
        except Exception as e:
            logger.warning(f"⚠️ SSL configuration failed: {str(e)}")
            return ssl._create_unverified_context()

    def _configure_ssl(self) -> None:
        """Configure secure SSL context for Exchange connection."""
        try:
            # Create a custom SSL context that uses system certificates
            ssl_ctx = create_urllib3_context()
            ssl_ctx.load_default_certs()

            # Configure exchangelib to use our secure context
            class SecureAdapter(BaseProtocol.HTTP_ADAPTER_CLS):
                ssl_context = ssl_ctx

            BaseProtocol.HTTP_ADAPTER_CLS = SecureAdapter
            logger.info("✅ SSL configured with system certificates")

        except Exception as e:
            logger.warning(f"⚠️ SSL configuration warning: {str(e)}")
            logger.warning("Falling back to certificate verification with warnings")
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _connect_to_exchange(self):
        """Connect to Exchange server with provided credentials."""
        try:
            # Create credentials in DOMAIN\username format
            full_username = f"{self.config['domain']}\\{self.config['username']}"
            credentials = Credentials(username=full_username, password=self.config["password"])

            # Configure Exchange version (Exchange 2016 CU22+)
            version = Version(build=Build(15, 1, 2248, 0))

            # Get email domain from config or construct it
            email_domain = self.config.get("email_domain")
            if email_domain is None:
                raise ValueError("`email_domain` must configured!")
            primary_email = f"{self.config['username']}@{email_domain}"

            # Create configuration
            config = Configuration(
                service_endpoint=f"https://{self.config['server']}/EWS/Exchange.asmx",
                credentials=credentials,
                auth_type=self.config["auth_type"],
                version=version,
            )

            # Connect to account
            account = Account(
                primary_smtp_address=primary_email,
                config=config,
                autodiscover=False,
                access_type=DELEGATE,
            )

            if account.protocol:
                ssl_context = self._create_ssl_context()
                adapter = SecureHTTPAdapter(ssl_context=ssl_context)
                # Mount the adapter to the account's session for HTTPS requests
                account.protocol.session.mount("https://", adapter)

            if self.verbose:
                print("✅ Connected to Exchange Server")
            logger.info("Successfully connected to Exchange Server")
            return account

        except UnauthorizedError as e:
            raise AuthenticationError(f"Authentication failed: {str(e)}") from e
        except TransportError as e:
            raise ExchangeEmailConnectionError(f"Connection failed: {str(e)}") from e
        except Exception as e:
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
            if template is None or template == TemplateType.PLAIN:
                # No template - use body as-is
                formatted_body = body
            else:
                # Get template (handles both TemplateType enum and string names)
                template_html = get_template(template)

                # Apply template variables if provided
                if template_vars:
                    for key, value in template_vars.items():
                        body = body.replace(f"{{{key}}}", str(value))

                # Format body with template
                formatted_body = template_html.replace("{body}", body)

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

                    except Exception as e:
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
            if self.verbose:
                print(f"✅ Email sent successfully to {', '.join(recipients)}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")
            if self.verbose:
                print(f"❌ Failed to send email: {str(e)}")
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup resources if needed
        pass
