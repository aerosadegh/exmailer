# Exceptions

ExMailer defines a hierarchy of exceptions to facilitate precise error handling.
All custom exceptions inherit from the base class `ExchangeEmailerError`, which
itself extends Python's built-in `Exception`.

## Inheritance Hierarchy

```
Exception
└── ExchangeEmailerError
    ├── AuthenticationError
    ├── ExchangeEmailConnectionError
    ├── SendError
    ├── AttachmentError
    └── ConfigurationError
```

## Exception Reference

### `ExchangeEmailerError`

The base exception class for the ExMailer package. Catch this type to handle
any ExMailer-related error in a single `except` block.

---

### `AuthenticationError`

**Inherits from:** `ExchangeEmailerError`

Raised when authentication to the Exchange server fails, such as when NTLM
negotiation is rejected or credentials are invalid.

---

### `ExchangeEmailConnectionError`

**Inherits from:** `ExchangeEmailerError`

Raised when a connection to the Exchange server cannot be established, for
example when the server is unreachable or the hostname cannot be resolved.

---

### `SendError`

**Inherits from:** `ExchangeEmailerError`

Raised when sending an email or calendar item fails after a successful
connection has been made.

---

### `AttachmentError`

**Inherits from:** `ExchangeEmailerError`

Raised when attachment processing fails, such as when an attachment file is
missing, unreadable, or exceeds server limits.

---

### `ConfigurationError`

**Inherits from:** `ExchangeEmailerError`

Raised when the ExMailer configuration is missing or malformed, for example
when required fields are absent from the configuration object.

---

## Usage Example

```python
from exmailer import ExMailer
from exmailer.exceptions import (
    ExchangeEmailerError,
    AuthenticationError,
    ExchangeEmailConnectionError,
    SendError,
    AttachmentError,
    ConfigurationError,
)

try:
    mailer = ExMailer(config)
    mailer.send(
        to=["recipient@example.com"],
        subject="Hello",
        body="World",
        attachments=["/path/to/report.pdf"],
    )
except ConfigurationError as e:
    # Config object is missing required fields or is malformed
    print(f"Configuration error: {e}")
except AuthenticationError as e:
    # NTLM negotiation failed or credentials were rejected
    print(f"Authentication error: {e}")
except ExchangeEmailConnectionError as e:
    # Exchange server is unreachable
    print(f"Connection error: {e}")
except AttachmentError as e:
    # Attachment file is missing or could not be read
    print(f"Attachment error: {e}")
except SendError as e:
    # Message was constructed but delivery failed
    print(f"Send error: {e}")
except ExchangeEmailerError as e:
    # Catch-all for any other ExMailer exception
    print(f"Unexpected ExMailer error: {e}")
```
