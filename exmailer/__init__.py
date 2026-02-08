from .core import ExchangeEmailer
from .exceptions import (
    AttachmentError,
    AuthenticationError,
    ConfigurationError,
    ExchangeEmailConnectionError,
)
from .templates import get_default_template, get_persian_template, register_custom_template

__version__ = "1.0.0"
__author__ = "Sadegh Yazdani"
__all__ = [
    "ExchangeEmailer",
    "get_default_template",
    "get_persian_template",
    "register_custom_template",
    "AuthenticationError",
    "ExchangeEmailConnectionError",
    "AttachmentError",
    "ConfigurationError",
]
