# Quick Start

Get up and running with ExMailer in minutes. This guide assumes you have already installed the package.

## Basic Usage

The most robust way to use ExMailer is via the context manager, which ensures proper resource handling.

```python
from exmailer import ExchangeEmailer

# Minimal example using environment variables for config
with ExchangeEmailer() as emailer:
    emailer.send_email(
        subject="Hello from ExMailer",
        body="This is a test email sent via Microsoft Exchange.",
        recipients=["colleague@company.com"]
    )
```

## Using the CLI
ExMailer provides a powerful command-line interface for quick tasks or shell scripting.

```Bash
# Basic command to send an email
exmailer --subject "Test Subject" --body "Hello World" --to user@company.com
```

Note: For the CLI to work, ensure you have an `exmailer.json` file in your current directory or your environment variables set.
