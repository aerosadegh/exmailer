# Ex<span style="color:gray">change E</span>mailer

<div align="center">
  <p><strong>Send emails via Microsoft Exchange Server with HTML template support</strong></p>
  <p>
    <a href="https://pypi.org/project/exmailer/"><img src="https://img.shields.io/pypi/v/exmailer.svg" alt="PyPI"></a>
    <a href="https://pypi.org/project/exmailer/"><img src="https://img.shields.io/pypi/pyversions/exmailer.svg" alt="Python Versions"></a>
    <a href="https://github.com/aerosadegh/exmailer/blob/main/LICENSE"><img src="https://img.shields.io/github/license/aerosadegh/exmailer.svg" alt="License"></a>
  </p>
</div>

---

## Overview

ExMailer is a Python library designed to simplify sending emails through Microsoft Exchange Server with full support for HTML text formatting.

## Key Features

- :fontawesome-solid-server: **Microsoft Exchange Integration** - Seamless NTLM authentication
- :fontawesome-solid-language: **Bi-directional Language Support** - Persian (RTL) and English (LTR) templates
- :fontawesome-solid-palette: **Professional HTML Templates** - Customizable email templates
- :fontawesome-solid-paperclip: **Attachment Support** - Multiple files with automatic MIME detection
- :fontawesome-solid-gear: **Flexible Configuration** - Environment variables, JSON, or programmatic setup
- :fontawesome-solid-terminal: **CLI Interface** - Command-line tool for quick operations
- :fontawesome-solid-lock: **Secure SSL/TLS** - Certificate verification and encryption
- :fontawesome-solid-bug: **Error Handling** - Custom exceptions for debugging

## Quick Example

=== "Python"

```python
from exmailer import ExchangeEmailer

with ExchangeEmailer() as emailer:
    emailer.send_email(
        subject="سلام دنیا",  # Hello World in Persian
        body="این یک ایمیل تستی است",
        recipients=["colleague@company.com"],
        is_persian=True
    )
```
