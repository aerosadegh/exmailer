# Basic Usage

This guide covers the core methods of sending emails and managing the `ExchangeEmailer` instance.

## Connecting to Exchange

The library handles NTLM authentication and patches `exchangelib` to use system SSL certificates for secure connections.

```python
from exmailer import ExchangeEmailer

# Initialize with a specific config dictionary
config = {
    "domain": "CORP",
    "username": "user",
    "password": "pass",
    "server": "mail.corp.com",
    "email_domain": "corp.com"
}

emailer = ExchangeEmailer(config=config)
```

### Use the exmailer to Sending to Multiple Recipients
You can provide a list of email addresses for recipients, CC, and BCC.


```Python
emailer.send_email(
    subject="Team Update",
    body="Project status is green.",
    recipients=["lead@company.com", "manager@company.com"],
    cc_recipients=["team@company.com"],
    bcc_recipients=["archive@company.com"]
)
```

### Using `f-string` style body formatting
If you use a template, you can pass variables to be dynamically replaced in the body.

```Python
emailer.send_email(
    subject="Alert",
    body="The server {server_name} is {status}.",
    recipients=["admin@company.com"],
    template_vars={"server_name": "DB-01", "status": "DOWN"}
)
```
