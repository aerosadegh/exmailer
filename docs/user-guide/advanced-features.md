# Advanced Features

## Dynamic Variable Interpolation

ExMailer supports `f-string` style placeholders in your email body or template.

```python
emailer.send_email(
    subject="System Alert",
    body="Node {node_id} reported status: {status}",
    recipients=["admin@company.com"],
    template_vars={"node_id": "SRV-01", "status": "CRITICAL"}
)
```

> **Warning: Escaping literal braces**
>
> If your email body contains literal `{` or `}` characters that are **not** meant to be
> template variable placeholders — for example, inline CSS rules or JavaScript snippets —
> you must escape them by doubling the brace: `{{` and `}}`.
>
> ```python
> emailer.send_email(
>     subject="Styled Alert",
>     # Literal CSS braces are escaped; {status} is still interpolated.
>     body="<style>p {{ color: red; }}</style><p>Status: {status}</p>",
>     recipients=["admin@company.com"],
>     template_vars={"status": "CRITICAL"}
> )
> ```

## Custom Template Engine

You can define high-fidelity HTML templates with CSS and register them for reuse.

1. **Define the Template** — Use `{body}` as the placeholder for the email content.
   Because templates are processed through `str.format()`, all CSS block braces must be
   escaped as `{{` and `}}`.
2. **Register** — Use `register_custom_template` to make the template available by name.
3. **Execute** — Reference the template by name in `send_email`.

```python
from exmailer import ExchangeEmailer, TemplateType

CORPORATE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 8px; padding: 32px; }}
    .footer {{ margin-top: 24px; font-size: 12px; color: #888; }}
  </style>
</head>
<body>
  <div class="container">
    {body}
    <div class="footer">This message was sent automatically. Please do not reply.</div>
  </div>
</body>
</html>"""

emailer = ExchangeEmailer(verbose=False)

# Register once at startup
emailer.register_custom_template("corporate", CORPORATE_TEMPLATE)

# Use by name in any send call
emailer.send_email(
    subject="Quarterly Report",
    body="<p>Please find the quarterly summary attached.</p>",
    recipients=["finance@company.com"],
    template="corporate",
)
```

## Configurable Debug Logging

When `verbose=True`, ExMailer writes detailed Exchange protocol traffic to a log file.
By default that file is named `exchange_debug.log` in the current working directory.
Use the `log_file` parameter to point it elsewhere:

```python
emailer = ExchangeEmailer(
    verbose=True,
    log_file="logs/exchange_debug.log",
)
```

The parent directory must already exist. `log_file` has no effect when `verbose=False`.

## Targeting a Specific Exchange Version

ExMailer communicates with Exchange using a specific server build version that is sent
in every EWS request. By default this is set to Exchange 2016 CU3
(`[15, 1, 1415, 2]`). If your server rejects requests or behaves unexpectedly, you can
override this via the `exchange_build` key in your configuration file:

```toml
# exmailer.toml (or the [exmailer] section of pyproject.toml)
exchange_build = [15, 1, 2248, 0]   # Exchange 2019 CU1
```

The value must be a four-element list of integers in the form
`[major, minor, build, revision]` matching the version string reported by your
Exchange server.
