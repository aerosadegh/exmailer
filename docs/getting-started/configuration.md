# Configuration Guide

ExMailer provides flexible configuration options to connect to your Microsoft Exchange server. You can configure it through multiple methods, which are applied in the following priority order (highest to lowest):

1. **Programmatic configuration** (highest priority)
2. **Explicit config file path**
3. **Auto-discovered config files**
4. **Environment variables**

## Configuration Methods

### Method 1: Programmatic Configuration (Recommended for Scripts)

Pass configuration directly as a dictionary when initializing `ExchangeEmailer`:

```python
from exmailer import ExchangeEmailer

emailer = ExchangeEmailer(config={
    "domain": "your-domain",
    "username": "john.doe",
    "password": "your-password",
    "server": "mail.yourcompany.com",
    "email_domain": "yourcompany.com",
    "auth_type": "NTLM",
    "save_copy": True
})
```

### Method 2: Explicit config file path

You must put the examples in below directory:
path priorities:
    1. `exmailer.json`
    2. `exmailer.yaml`
    3. `~/.config/exmailer/config.json`
    4. `~/.config/exmailer/exmailer.json`
    5. `~/.config/exmailer/exmailer.json`

#### Example: `exmailer.json`

```json
{
  "domain": "CORP",
  "username": "john.doe",
  "password": "your-password",
  "server": "mail.company.com",
  "email_domain": "company.com",
  "save_copy": true
}
```

#### Set environment variables `.env`:
```bash
EXCHANGE_DOMAIN="CORP"
EXCHANGE_USER="jdoe"
EXCHANGE_PASS="secret_password"
EXCHANGE_SERVER="mail.corp.com"
EXCHANGE_EMAIL_DOMAIN="corp.com"
EXCHANGE_AUTH_TYPE="NTLM" # or BASIC
EXCHANGE_SAVE_COPY="true"
```

#### Yaml: `exmailer.yaml`

```yaml
domain: "CORP",
username: "john.doe",
password: "your-password",
server: "mail.company.com",
email_domain: "company.com",
save_copy: true
```
