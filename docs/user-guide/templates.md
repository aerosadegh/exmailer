# Templates

ExMailer provides a flexible HTML template system to ensure professional-looking emails without writing HTML in every script.

## Built-in Templates

The library includes two primary layouts:

1. **`TemplateType.DEFAULT`**: English (LTR) layout.
2. **`TemplateType.PERSIAN`**: Persian (RTL) layout.
3. **`TemplateType.PLAIN`**: No HTML wrapper (raw content)\.

## Custom Templates

You can register your own HTML layouts using the `{body}` placeholder.

```python
from exmailer import register_custom_template, ExchangeEmailer

# 1. Define and register
my_layout = "<html><body><h1>Alert</h1><div>{body}</div></body></html>"
register_custom_template("alert_theme", my_layout)

# 2. Use by name
with ExchangeEmailer() as emailer:
    emailer.send_email(
        subject="Custom Template",
        body="This content goes into the body placeholder.",
        recipients=["user@company.com"],
        template="alert_theme"
    )
```
