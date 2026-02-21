# Exceptions
ExMailer defines a hierarchy of exceptions to facilitate precise error handling.

* ExMailerError: The base exception class.

* ConfigurationError: Raised when the configuration is missing or malformed.

* AuthenticationError: Raised when NTLM or credentials fail.

* ConnectionError: Raised when the Exchange server is unreachable.

* TemplateError: Raised when a requested template is not found or variable interpolation fails.
