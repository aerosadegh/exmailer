# Templates API Reference

The `exmailer.templates` module manages the built-in HTML email templates and allows you to register your own.

---

## `TemplateType` Enum

An enumeration of the built-in template identifiers.

| Member | Description |
|--------|-------------|
| `TemplateType.DEFAULT` | A clean left-to-right (LTR) layout suitable for English and other Western-script content. |
| `TemplateType.PERSIAN` | A right-to-left (RTL) layout with Persian/Arabic typography and font settings. |
| `TemplateType.PLAIN` | No wrapper — the body is sent as-is with no surrounding HTML template. |

---

## Functions

### `register_custom_template(name: str, template_html: str) -> None`

Registers a custom HTML template for use throughout the current application session.

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | A unique identifier for the template. Used to retrieve it later via `get_template()`. |
| `template_html` | `str` | A valid HTML string that **must** contain a `{body}` placeholder where the email body will be injected. |

**Raises**

- `ValueError` — if `template_html` does not contain the `{body}` placeholder.

---

### `get_template(template: TemplateType | str) -> str`

Returns the HTML template string for the given identifier.

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `template` | `TemplateType \| str` | A `TemplateType` enum member or a string alias (see table below). |

**Built-in string aliases**

| Aliases | Resolves to |
|---------|-------------|
| `"default"`, `"english"`, `"ltr"`, `"en"` | `TemplateType.DEFAULT` |
| `"persian"`, `"farsi"`, `"rtl"`, `"fa"` | `TemplateType.PERSIAN` |
| `"minimal"`, `"simple"` | A minimal wrapper template |
| `"plain"`, `"none"` | `TemplateType.PLAIN` (no wrapper) |

**Raises**

- `KeyError` — if a string is passed that does not match any built-in alias or registered custom template name.

---

### `list_custom_templates() -> list[str]`

Returns the names of all templates that have been registered in the current session via `register_custom_template()`.

**Returns:** `list[str]` — an empty list if no custom templates have been registered.

---

### `get_persian_template() -> str`

Returns the raw HTML string for the built-in Persian (RTL) template. The template includes right-to-left directionality, Persian-compatible fonts, and appropriate text alignment.

---

### `get_default_template() -> str`

Returns the raw HTML string for the built-in default (LTR) template. Suitable for English and other left-to-right languages.

---

### `get_minimal_template() -> str`

Returns the raw HTML string for the built-in minimal template. Provides a lightweight wrapper with minimal styling — useful when you want basic structure without opinionated design.

---

## Example: Registering and Using a Custom Template

```python
from exmailer import ExchangeEmailer
from exmailer.templates import register_custom_template

BRANDED_TEMPLATE = """
<html>
  <body style="font-family: Arial, sans-serif; background: #f5f5f5;">
    <div style="max-width: 600px; margin: auto; background: white; padding: 24px;">
      <img src="https://example.com/logo.png" alt="Logo" width="120" />
      <hr />
      {body}
      <hr />
      <p style="font-size: 11px; color: #999;">© 2025 Example Corp</p>
    </div>
  </body>
</html>
"""

register_custom_template("branded", BRANDED_TEMPLATE)

with ExchangeEmailer() as mailer:
    mailer.send_email(
        subject="Monthly Report",
        body="<p>Please find the report attached.</p>",
        recipients=["colleague@example.com"],
        template="branded",
    )
```

> **Tip:** If your template or body contains literal `{` or `}` characters (e.g. inline CSS), escape them as `{{` and `}}` so they are not treated as `str.format()` placeholders.
