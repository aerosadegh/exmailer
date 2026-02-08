"""Tests for core ExchangeEmailer functionality (with mocked Exchange server)."""

import ssl
import pytest
from exchangelib.protocol import BaseProtocol

from exmailer.core import ExchangeEmailer, SecureHTTPAdapter
from exmailer.exceptions import AuthenticationError, ExchangeEmailConnectionError, SendError
from exmailer.templates import TemplateType
from exmailer.utils import validate_attachments


def test_secure_adapter_sets_context():
    ctx = ssl.create_default_context()
    adapter = SecureHTTPAdapter(ssl_context=ctx)
    assert adapter.ssl_context is ctx


def test_init_with_programmatic_config(mock_exchange_connection, sample_config):
    """Test initializing with programmatic config dict."""
    emailer = ExchangeEmailer(config=sample_config)

    assert emailer.config["domain"] == "company"
    assert emailer.config["username"] == "john.doe"

    assert mock_exchange_connection["account"].called

    # Compare against the patched adapter in exmailer.core
    import exmailer.core as core_module

    assert BaseProtocol.HTTP_ADAPTER_CLS is core_module.SecureHTTPAdapter


def test_init_with_config_file(mock_exchange_connection, config_file):
    """Test initializing with config file path."""
    emailer = ExchangeEmailer(config_path=config_file)
    assert emailer.config["domain"] == "company"
    assert emailer.config["server"] == "mail.company.com"


def test_send_email_with_persian_template(mock_exchange_connection, sample_config):
    """Test sending email with Persian RTL template."""
    emailer = ExchangeEmailer(config=sample_config)

    success = emailer.send_email(
        subject="تست",
        body="متن پیام فارسی",
        recipients=["recipient@company.com"],
        cc_recipients=["recipient@company.com"],
        bcc_recipients=["recipient@company.com"],
        template=TemplateType.PERSIAN,
    )
    assert validate_attachments([]) == []

    assert success is True

    # Retrieve the arguments passed to the Message constructor
    message_cls = mock_exchange_connection["message_cls"]
    _, kwargs = message_cls.call_args

    # Check body content (converted to string to handle HTMLBody wrapper)
    body_str = str(kwargs["body"])
    assert "direction: rtl" in body_str or 'dir="rtl"' in body_str
    assert "متن پیام فارسی" in body_str

    # Verify send was called
    message_instance = mock_exchange_connection["message_instance"]
    assert message_instance.send.called


def test_send_email_with_english_template(mock_exchange_connection, sample_config):
    """Test sending email with English LTR template."""
    emailer = ExchangeEmailer(config=sample_config)

    success = emailer.send_email(
        subject="Test",
        body="English message content",
        recipients=["recipient@company.com"],
        template=TemplateType.DEFAULT,
    )

    assert success is True

    message_cls = mock_exchange_connection["message_cls"]
    _, kwargs = message_cls.call_args
    body_str = str(kwargs["body"])

    assert "English message content" in body_str
    assert 'dir="rtl"' not in body_str


def test_send_email_plain_text(mock_exchange_connection, sample_config):
    """Test sending email without template (plain HTML)."""
    emailer = ExchangeEmailer(config=sample_config)

    success = emailer.send_email(
        subject="Plain",
        body="<p>Raw HTML content</p>",
        recipients=["recipient@company.com"],
        template=None,
    )

    assert success is True

    message_cls = mock_exchange_connection["message_cls"]
    _, kwargs = message_cls.call_args
    body_str = str(kwargs["body"])

    assert "<p>Raw HTML content</p>" in body_str


def test_send_email_with_attachments(mock_exchange_connection, sample_config, tmp_path):
    """Test sending email with attachments."""
    attachment = tmp_path / "report.pdf"
    attachment.write_bytes(b"PDF content")

    emailer = ExchangeEmailer(config=sample_config)

    success = emailer.send_email(
        subject="With Attachment",
        body="See attached file",
        recipients=["recipient@company.com"],
        attachments=[str(attachment)],
    )

    assert success is True

    # Verify attach was called on the instance
    message_instance = mock_exchange_connection["message_instance"]
    assert message_instance.attach.called

    # Verify file content
    call_args = message_instance.attach.call_args
    file_attachment = call_args[0][0]
    assert file_attachment.name == "report.pdf"
    assert file_attachment.content == b"PDF content"


def test_send_email_failure_raises_senderror(mock_exchange_connection, sample_config):
    """Test that send failures properly raise SendError."""
    # Configure the message instance to raise exception on send()
    message_instance = mock_exchange_connection["message_instance"]
    message_instance.send.side_effect = Exception("SMTP timeout after 30s")

    emailer = ExchangeEmailer(config=sample_config)

    with pytest.raises(SendError) as exc_info:
        emailer.send_email(
            subject="Test",
            body="Body",
            recipients=["user@company.com"],
        )

    assert "SMTP timeout" in str(exc_info.value)


def test_authentication_failure_raises_error(mock_exchange_connection, sample_config):
    """Test that authentication failures raise AuthenticationError."""
    from exchangelib.errors import UnauthorizedError

    mock_exchange_connection["account"].side_effect = UnauthorizedError("Invalid credentials")

    with pytest.raises(AuthenticationError) as exc_info:
        ExchangeEmailer(config=sample_config)

    assert "Authentication failed" in str(exc_info.value)


def test_connection_failure_raises_error(mock_exchange_connection, sample_config):
    """Test that connection failures raise ExchangeEmailConnectionError."""
    from exchangelib.errors import TransportError

    mock_exchange_connection["account"].side_effect = TransportError("Connection refused")

    with pytest.raises(ExchangeEmailConnectionError) as exc_info:
        ExchangeEmailer(config=sample_config)

    assert "Connection failed" in str(exc_info.value)
