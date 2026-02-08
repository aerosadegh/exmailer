# Ex(change E)mailer 🐍

<div align="center">
  <p><strong>Enterprise-Grade Microsoft Exchange Email Client with HTML Template Support</strong></p>
  <p>
    <a href="https://pypi.org/project/exmailer/"><img src="https://img.shields.io/pypi/v/exmailer.svg" alt="PyPI"></a>
    <a href="https://pypi.org/project/exmailer/"><img src="https://img.shields.io/pypi/pyversions/exmailer.svg" alt="Python Versions"></a>
    <a href="https://github.com/aerosadegh/exmailer/actions"><img src="https://github.com/aerosadegh/exmailer/workflows/Publish%20to%20PyPI/badge.svg" alt="Build Status"></a>
    <a href="https://github.com/aerosadegh/exmailer/blob/main/LICENSE"><img src="https://img.shields.io/github/license/aerosadegh/exmailer.svg" alt="License"></a>
  </p>
</div>

**ExMailer** is a robust Python library designed for robust interaction with Microsoft Exchange Servers (EWS). It solves the complexity of NTLM authentication and provides a flexible, HTML templating engine out of the box.

## Features

- **Microsoft Exchange Integration**: Seamless connection to Exchange servers using NTLM authentication
- **Rich Email Formatting**: Professional HTML email templates with customizable variables
- **Attachment Support**: Handle multiple file attachments with automatic MIME type detection
- **Flexible Configuration**: Support for environment variables, JSON config files, or programmatic setup
- **CLI Interface**: Command-line tool for quick email sending
- **Comprehensive Error Handling**: Custom exceptions for different failure scenarios
- **Secure SSL/TLS**: Proper certificate verification and secure connections
- **Logging Support**: Verbose mode for debugging and troubleshooting

## Installation

Requires Python 3.11+

```bash
pip install exmailer
```


## Quick Start

### Using Python API

```python
from exmailer import ExchangeEmailer

with ExchangeEmailer() as emailer:
    emailer.send_email(
        subject="گزارش هفتگی",
        body="لطفاً گزارش پیوست شده را بررسی نمایید.",
        recipients=["manager@company.com"],
        template=TemplateType.PERSIAN,  # Uses built-in RTL template
        attachments="./report.pdf",
    )

    # Send a standard English/LTR email
    emailer.send_email(
        subject="Weekly Report",
        body="Please find attached.",
        recipients=["colleague@company.com"],
        template=TemplateType.DEFAULT
        attachments="./report.pdf",
    )
```

#### Custom Templates
You can register custom HTML layouts for newsletters or alerts:
```python
from exmailer import ExchangeEmailer, register_custom_template

html_layout = """
<div style="border: 1px solid #ccc; padding: 20px;">
    <h1 style="color: navy;">Company Alert</h1>
    {body}
    <hr>
    <small>Confidential</small>
</div>
"""

register_custom_template("alert", html_layout)

with ExchangeEmailer() as emailer:
    emailer.send_email(
        subject="Server Down",
        body="<p>The main database is unreachable.</p>",
        recipients=["devops@company.com"],
        template="alert"  # Use the registered name
    )
```

### Using CLI (Under Construction)

```bash
python -m exchange_emailer \
    --subject "Weekly Report" \
    --body "Report content here" \
    --to recipient@company.com \
    --attachments ./report.pdf
```

## Configuration
ExMailer looks for `exmailer.json` or `exmailer.yaml` in your current directory or `~/.config/exmailer/`.

Set environment variables `.env`:

```bash
EXCHANGE_DOMAIN="CORP"
EXCHANGE_USER="jdoe"
EXCHANGE_PASS="secret_password"
EXCHANGE_SERVER="mail.corp.com"
EXCHANGE_EMAIL_DOMAIN="corp.com"
EXCHANGE_AUTH_TYPE="NTLM" # or BASIC
```

Or use a JSON config file `exmailer.json`:

```json
{
  "domain": "CORP",
  "username": "jdoe",
  "password": "secret_password",
  "server": "mail.corp.com",
  "email_domain": "corp.com",
  "auth_type": "NTLM",
  "save_copy": true
}
```

## Requirements

- Python 3.10+
- Microsoft Exchange Server access
- Valid domain credentials

## Author

Sadegh Yazdani

## License

GNU General Public License v3 (GPLv3)

