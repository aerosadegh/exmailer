# Ex(change E)mailer

A Python package for sending emails via Microsoft Exchange Server with HTML templates.

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
```bash
pip install exmailer

## Quick Start

### Using Python API

python
from exmailer import ExchangeEmailer

with ExchangeEmailer() as emailer:
    emailer.send_email(
        subject="Meeting Reminder",
        body="Please attend the meeting at 3 PM",
        recipients=["colleague@company.com"],
        is_persian=True,
        template_vars={"date": "1404/11/18"}
    )
```

### Using CLI

```bash
python -m exchange_emailer \
    --subject "Weekly Report" \
    --body "Report content here" \
    --to recipient@company.com \
    --attachments report.pdf \
    --persian
```

## Configuration

Set environment variables:


```bash
export EXCHANGE_DOMAIN="your-domain"
export EXCHANGE_USER="your-username"
export EXCHANGE_PASS="your-password"
export EXCHANGE_SERVER="mail.yourcompany.com"
```

Or use a JSON config file:

```json
{
"domain": "your-domain",
"username": "your-username",
"password": "your-password",
"server": "mail.yourcompany.com",
"auth_type": "NTLM",
"save_copy": true
}
```

## Requirements

- Python 3.8+
- Microsoft Exchange Server access
- Valid domain credentials

## Author

Sadegh Yazdani

## License

GNUv3 License

