"""Tests for custom exception handling."""

from exmailer.exceptions import (
    AttachmentError,
    AuthenticationError,
    ConfigurationError,
    ExchangeEmailConnectionError,
    ExchangeEmailerError,
)


def test_base_exception_hierarchy():
    """Test that all custom exceptions inherit from base."""
    assert issubclass(AuthenticationError, ExchangeEmailerError)
    assert issubclass(ExchangeEmailConnectionError, ExchangeEmailerError)
    assert issubclass(AttachmentError, ExchangeEmailerError)
    assert issubclass(ConfigurationError, ExchangeEmailerError)


def test_authentication_error():
    """Test AuthenticationError properties."""
    exc = AuthenticationError("Invalid credentials")
    assert str(exc) == "Invalid credentials"
    assert isinstance(exc, ExchangeEmailerError)


def test_connection_error():
    """Test ExchangeEmailConnectionError properties."""
    exc = ExchangeEmailConnectionError("Server unreachable")
    assert str(exc) == "Server unreachable"
    assert isinstance(exc, ExchangeEmailerError)


def test_attachment_error():
    """Test AttachmentError properties."""
    exc = AttachmentError("File not found: missing.pdf")
    assert "missing.pdf" in str(exc)
    assert isinstance(exc, ExchangeEmailerError)


def test_configuration_error():
    """Test ConfigurationError properties."""
    exc = ConfigurationError("Missing EXCHANGE_SERVER")
    assert "EXCHANGE_SERVER" in str(exc)
    assert isinstance(exc, ExchangeEmailerError)
