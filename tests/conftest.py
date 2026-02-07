"""Shared pytest fixtures and mocks for exmailer tests."""

import json
import os
from unittest.mock import MagicMock, patch
import pytest
from exchangelib import Account, Configuration, Credentials
from exmailer.core import ExchangeEmailer


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment variables before each test."""
    original_env = os.environ.copy()
    for key in list(os.environ.keys()):
        if key.startswith("EXCHANGE_"):
            del os.environ[key]
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def mock_ssl_and_adapter():
    """Globally mock SSL context creation and SecureHTTPAdapter."""
    with patch("exmailer.core.ssl.create_default_context") as mock_ssl, patch(
        "exmailer.core.SecureHTTPAdapter"
    ) as mock_adapter:

        mock_ctx = MagicMock()
        mock_ssl.return_value = mock_ctx
        mock_adapter_instance = MagicMock()
        mock_adapter.return_value = mock_adapter_instance

        yield {"ssl_context": mock_ctx, "adapter": mock_adapter_instance}


@pytest.fixture
def mock_exchange_account():
    """Mock Exchange account connection."""
    mock_account = MagicMock(spec=Account)
    mock_account.primary_smtp_address = "test@company.com"

    # Mock protocol and session for the new mounting logic
    mock_protocol = MagicMock()
    mock_session = MagicMock()
    mock_protocol.session = mock_session
    mock_account.protocol = mock_protocol

    return mock_account


@pytest.fixture
def mock_exchange_connection(mock_exchange_account):
    """Mock the entire Exchange connection process, including the Message class."""
    with patch("exmailer.core.Credentials", spec=Credentials) as mock_creds, patch(
        "exmailer.core.Configuration", spec=Configuration
    ) as mock_config, patch(
        "exmailer.core.Account", return_value=mock_exchange_account
    ) as mock_account_cls, patch(
        "exmailer.core.Message"
    ) as mock_message_cls:  # <--- NEW: Mock Message class

        mock_creds.return_value = MagicMock()
        mock_config.return_value = MagicMock()

        # Setup the Message instance that will be returned when Message() is called
        mock_message_instance = mock_message_cls.return_value
        mock_message_instance.send = MagicMock()
        mock_message_instance.attach = MagicMock()

        yield {
            "credentials": mock_creds,
            "configuration": mock_config,
            "account": mock_account_cls,
            "mock_account": mock_exchange_account,
            "message_cls": mock_message_cls,  # Return class to check constructor args
            "message_instance": mock_message_instance,  # Return instance to check send() calls
        }


@pytest.fixture
def sample_config():
    """Sample valid configuration."""
    return {
        "domain": "company",
        "username": "john.doe",
        "password": "secure_password",
        "server": "mail.company.com",
        "email_domain": "company.com",
        "auth_type": "NTLM",
        "save_copy": True,
    }


@pytest.fixture
def config_file(tmp_path):
    """Create a temporary valid config file."""
    config_path = tmp_path / "exmailer.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "domain": "company",
                "username": "john.doe",
                "password": "secure_password",
                "server": "mail.company.com",
                "email_domain": "company.com",
                "auth_type": "NTLM",
                "save_copy": True,
            },
            f,
        )
    return str(config_path)


@pytest.fixture
def minimal_config_env():
    """Set minimal required environment variables."""
    os.environ["EXCHANGE_DOMAIN"] = "company"
    os.environ["EXCHANGE_USER"] = "john.doe"
    os.environ["EXCHANGE_PASS"] = "secure_password"
    os.environ["EXCHANGE_SERVER"] = "mail.company.com"
    os.environ["EXCHANGE_EMAIL_DOMAIN"] = "company.com"
    return os.environ
