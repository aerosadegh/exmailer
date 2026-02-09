from .core import ExchangeEmailer
from .exceptions import (
    AttachmentError,
    AuthenticationError,
    ConfigurationError,
    ExchangeEmailConnectionError,
)
from .templates import get_default_template, get_persian_template, register_custom_template

try:
    from importlib.metadata import version

    __version__ = version("exmailer")
except Exception:  # pragma: no cover
    __version__ = "0.0.0-dev"

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
