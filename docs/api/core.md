# Core API Reference

The `exmailer` core module provides the primary interface for interacting with Microsoft Exchange.

## `ExchangeEmailer` Class

The main controller for email operations. It is designed to be used as a context manager to ensure connections are properly closed.

### Methods

#### `__init__(self, config: dict[str, Any] | None = None) -> None`
Initializes the emailer. If no config is provided, it attempts auto-discovery via environment variables or local files.

::: core.ExchangeEmailer
    handler: python
    options:
        show_root_heading: true
        show_source: true
        show_bases: true
        members: ["!^[A-Z]+$"]

#### `send_email(...) -> bool`
Sends an email through the Exchange server.

::: core.ExchangeEmailer.send_email
    handler: python
    options:
        show_root_heading: true
        show_source: true
        show_bases: true
        members: ["!^[A-Z]+$"]


| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `subject` | `str` | **Required** | The email subject line. |
| `body` | `str` | **Required** | The HTML or plain text body. |
| `recipients` | `list[str]` | **Required** | List of primary recipient addresses. |
| `cc_recipients` | `list[str] \| None` | `None` | List of CC addresses. |
| `bcc_recipients` | `list[str] \| None` | `None` | List of BCC addresses. |
| `template` | `TemplateType \| str \| None` | `TemplateType.DEFAULT` | The template to wrap the body in. |
| `template_vars` | `dict[str, Any] \| None` | `None` | Variables for f-string style replacement. |

---


## Template Management

### `register_custom_template(name: str, template_string: str) -> None`
Registers a new HTML template for global use within the application session.

---
