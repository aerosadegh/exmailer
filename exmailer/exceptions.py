class ExchangeEmailerError(Exception):
    """Base exception for Exchange Emailer package."""

    pass


class AuthenticationError(ExchangeEmailerError):
    """Raised when authentication to Exchange server fails."""

    pass


class ExchangeEmailConnectionError(ExchangeEmailerError):
    """Raised when connection to Exchange server fails."""

    pass


class SendError(ExchangeEmailerError):
    """Raised when connection to Exchange server fails."""

    pass


class AttachmentError(ExchangeEmailerError):
    """Raised when attachment processing fails."""

    pass


class ConfigurationError(ExchangeEmailerError):
    """Raised when configuration is invalid."""

    pass
