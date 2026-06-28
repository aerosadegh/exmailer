# Templates

ExMailer provides a flexible HTML template system to ensure professional-looking emails without writing HTML in every script.

## Built-in Templates

The library includes three layouts, selectable via the `TemplateType` enum or a string alias:

| Enum | String aliases | Description |
|---|---|---|
| `TemplateType.PERSIAN` | `"persian"`, `"farsi"`, `"rtl"`, `"fa"` | RTL layout with Persian font stack |
| `TemplateType.DEFAULT` | `"default"`, `"english"`, `"ltr"`, `"en"` | LTR layout with standard English styling |
| *(string only)* | `"minimal"`, `"simple"` | Minimal HTML wrapper, no header/footer |
| `TemplateType.PLAIN` | `"plain"`, `"none"` | No HTML wrapper — raw body content only |

The default template used by the CLI is `persian`.

---

## Using `TemplateType` Directly

`TemplateType` is exported from the top-level `exmailer` package and can be passed anywhere the `template=` parameter is accepted:

```python
from exmailer import ExchangeEmailer, TemplateType

with ExchangeEmailer() as emailer:
    emailer.send_email(
        subject="Weekly Update",
        body="Here is this week's summary.",
        recipients=["team@company.com"],
        template=TemplateType.DEFAULT,   # LTR English layout
    )
```

```python
from exmailer import ExchangeEmailer, TemplateType

with ExchangeEmailer() as emailer:
    emailer.send_email(
        subject="اطلاعیه هفتگی",
        body="خلاصه این هفته در زیر آمده است.",
        recipients=["team@company.com"],
        template=TemplateType.PERSIAN,   # RTL layout
    )
```

You can also pass any of the string aliases directly — these are equivalent:

```python
emailer.send_email(..., template="rtl")      # same as TemplateType.PERSIAN
emailer.send_email(..., template="english")  # same as TemplateType.DEFAULT
emailer.send_email(..., template="minimal")  # minimal wrapper
emailer.send_email(..., template="none")     # same as TemplateType.PLAIN
```

---

## Custom Templates

You can register your own HTML layouts using the `{body}` placeholder.

```python
from exmailer import ExchangeEmailer, TemplateType, register_custom_template

# 1. Define and register
my_layout = "<html><body><h1>Alert</h1><div>{body}</div></body></html>"
register_custom_template("alert_theme", my_layout)

# 2. Use by name
with ExchangeEmailer() as emailer:
    emailer.send_email(
        subject="Custom Template",
        body="This content goes into the body placeholder.",
        recipients=["user@company.com"],
        template="alert_theme",
    )
```

### Brace escaping in custom templates

Because ExMailer uses Python's `str.format_map()` to inject content into templates, any literal `{` or `}` character in your HTML that is **not** the `{body}` placeholder must be escaped by doubling it: `{{` and `}}`.

This most commonly applies to inline `<style>` or `<script>` blocks:

```python
my_layout = """
<html>
<head>
  <style>
    /* Use {{ and }} instead of { and } in CSS */
    .container {{
      max-width: 600px;
      margin: 0 auto;
    }}
  </style>
</head>
<body>
  <div class="container">{body}</div>
</body>
</html>
"""
register_custom_template("branded", my_layout)
```

The `{body}` placeholder itself is written normally — only unrelated braces need doubling.
