# Ex<span style="color:lightgray">change E</span>mailer

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

ExMailer is a Python library designed to simplify sending emails and scheduling meetings through Microsoft Exchange Server with full support for HTML text formatting.

## Key Features

- :fontawesome-regular-calendar: **Calendar Management** - Schedule, update, and cancel meetings natively
- :fontawesome-solid-server: **Microsoft Exchange Integration** - Seamless NTLM authentication
- :fontawesome-solid-language: **Bi-directional Language Support** - Persian (RTL) and English (LTR) templates
- :fontawesome-solid-palette: **Professional HTML Templates** - Customizable email and meeting templates
- :fontawesome-solid-paperclip: **Attachment Support** - Multiple files with automatic MIME detection
- :fontawesome-solid-gear: **Flexible Configuration** - Environment variables, JSON, or programmatic setup
- :fontawesome-solid-terminal: **CLI Interface** - Command-line tool for quick operations
- :fontawesome-solid-lock: **Secure SSL/TLS** - Certificate verification and encryption

## Quick Example

=== "Python (Email)"

    ```python
    from exmailer import ExchangeEmailer

    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="Hello There 👋🏻",
            body="<p>Test email</p>",
            recipients=["colleague@company.com"],
        )
    ```

=== "Python (Meeting)"

    ```python
    import datetime
    from exmailer import ExchangeEmailer

    with ExchangeEmailer() as emailer:
        emailer.send_meeting_invite(
            subject="Project Kickoff",
            start=datetime.datetime(2026, 6, 25, 10, 0),
            end=datetime.datetime(2026, 6, 25, 11, 0),
            required_attendees=["team@company.com"]
        )
    ```
