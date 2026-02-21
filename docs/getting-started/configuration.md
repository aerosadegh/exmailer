# Configuration Guide

ExMailer provides multiple ways to configure your connection to a Microsoft Exchange server. Settings are applied with the following priority (highest to lowest):

1. **Programmatic configuration** (dictionary passed directly to `ExchangeEmailer`)
2. **Explicit configuration file** (path provided via `config_file` parameter)
3. **Auto‑discovered configuration files** (searched in predefined locations)
4. **Environment variables**

All configuration methods expect the same set of parameters (see table below).

## Configuration Parameters

| Parameter      | Type    | Required | Default  | Description |
|----------------|---------|----------|----------|-------------|
| `domain`       | string  | Yes      | –        | Active Directory domain (e.g., `CORP`, `your-domain`) |
| `username`     | string  | Yes      | –        | User account name (without domain, e.g., `john.doe`) |
| `password`     | string  | Yes      | –        | Account password |
| `server`       | string  | Yes      | –        | Exchange server hostname or IP |
| `email_domain` | string  | Yes      | –        | Domain part of the email address (e.g., `company.com`) |
| `auth_type`    | string  | No       | `NTLM`   | Authentication method: `NTLM` or `BASIC` |
| `save_copy`    | boolean | No       | `false`  | Whether to save a copy of sent emails in the Sent Items folder |

> **Note on username format**
> The full user identifier used internally is `{domain}\{username}@{email_domain}`.
> For example: `CORP\john.doe@company.com`

---

## Method 1: Programmatic Configuration (Highest Priority)

Pass a dictionary directly when creating an `ExchangeEmailer` instance:

```python
from exmailer import ExchangeEmailer

config = {
    "domain": "CORP",
    "username": "john.doe",
    "password": "your-secret-password",
    "server": "mail.company.com",
    "email_domain": "company.com",
    "auth_type": "NTLM",       # optional
    "save_copy": True           # optional
}

emailer = ExchangeEmailer(config=config)
```

This method overrides any file‑based or environment configuration.

---

## Method 2: Configuration Files

You can store settings in a JSON or YAML file. Two approaches are supported:

### A. Explicit File Path (Medium Priority)

Pass the file path using the `config_file` parameter:

```python
emailer = ExchangeEmailer(config_file="/path/to/exmailer.json")
```

### B. Auto‑discovered Files (Lower Priority)

If no explicit path is given, ExMailer looks for configuration files in the following order (first found wins):

1. `./exmailer.json`
2. `./exmailer.yaml` / `./exmailer.yml`
3. `~/.config/exmailer/config.json`
4. `~/.config/exmailer/exmailer.json`
5. `~/.config/exmailer/config.yaml` / `~/.config/exmailer/config.yml`
6. `~/.config/exmailer/exmailer.yaml` / `~/.config/exmailer/exmailer.yml`

#### JSON Example (`exmailer.json`)

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

#### YAML Example (`exmailer.yaml`)

```yaml
domain: CORP
username: john.doe
password: your-password
server: mail.company.com
email_domain: company.com
save_copy: true
```

> YAML does not allow trailing commas – the example above is correct.

---

## Method 3: Environment Variables (Lowest Priority)

Set the following environment variables in your shell or a `.env` file (if you use `python-dotenv` or a similar loader):

```bash
EXCHANGE_DOMAIN="CORP"
EXCHANGE_USER="john.doe"
EXCHANGE_PASS="your-password"
EXCHANGE_SERVER="mail.company.com"
EXCHANGE_EMAIL_DOMAIN="company.com"
EXCHANGE_AUTH_TYPE="NTLM"      # optional, defaults to NTLM
EXCHANGE_SAVE_COPY="true"       # optional, defaults to false
```

Boolean values accept `true`/`false`, `yes`/`no`, `1`/`0` (case‑insensitive).

> Environment variables are only used if no configuration dictionary or file is supplied.

---

## Summary

| Priority | Method                  | How to Use                                                                 |
|----------|-------------------------|----------------------------------------------------------------------------|
| 1        | Programmatic dictionary | `ExchangeEmailer(config={...})`                                            |
| 2        | Explicit file           | `ExchangeEmailer(config_file="path/to/file")`                              |
| 3        | Auto‑discovered file    | Place a JSON/YAML file in one of the predefined locations                  |
| 4        | Environment variables   | Set `EXCHANGE_*` variables in your environment                             |

Choose the method that best fits your use case – programmatic for scripts, configuration files for deployment, and environment variables for containerized or ephemeral environments.
