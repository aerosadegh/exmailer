# Core API Reference

The `exmailer` core module provides the primary interface for interacting with Microsoft Exchange.

## `ExchangeEmailer` Class

The main controller for email operations. It is designed to be used as a context manager to ensure connections are properly closed.

### Methods

#### `__init__(self, config_path: str | None = None, config: dict[str, Any] | None = None, verbose: bool = False, log_file: str = "exchange_debug.log") -> None`
Initializes the emailer.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config_path` | `str \| None` | `None` | Path to a JSON/YAML config file. If omitted, falls back to `config` or environment-variable auto-discovery. |
| `config` | `dict[str, Any] \| None` | `None` | A configuration dictionary. Used when `config_path` is not provided. |
| `verbose` | `bool` | `False` | Enables debug-level logging to the log file. |
| `log_file` | `str` | `"exchange_debug.log"` | Path of the debug log file written when `verbose=True`. |

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
| `importance` | `"Low" \| "Normal" \| "High"` | `"Normal"` | Email importance/priority level. |
| `template` | `TemplateType \| str \| None` | `TemplateType.DEFAULT` | The template to wrap the body in. |
| `template_vars` | `dict[str, Any] \| None` | `None` | Variables for f-string style replacement. |

> **Note — `template_vars` substitution:** Keys in `template_vars` are substituted into the body using Python's `str.format()`. If your body contains literal `{` or `}` characters (e.g. inline CSS such as `color: rgb(0, 0, 0)`), escape them as `{{` and `}}` to prevent a `KeyError` or malformed output.


#### `send_meeting_invite(...) -> str`
::: core.ExchangeEmailer.send_meeting_invite
    handler: python
    options:
        show_root_heading: true
        show_source: true
        show_bases: true
        members: ["!^[A-Z]+$"]

#### `update_meeting_invite(...) -> bool`
::: core.ExchangeEmailer.update_meeting_invite
    handler: python
    options:
        show_root_heading: true
        show_source: true
        show_bases: true
        members: ["!^[A-Z]+$"]

> **Note — body & template interaction:** When `body` is provided, it is passed through `_render_body` together with the given `template` before being saved to the invite. This means the `template` and `body` parameters work together: the body content is rendered inside the chosen template wrapper, just as it is in `send_email`.

#### `cancel_meeting_invite(...) -> bool`
::: core.ExchangeEmailer.cancel_meeting_invite
    handler: python
    options:
        show_root_heading: true
        show_source: true
        show_bases: true
        members: ["!^[A-Z]+$"]
---


## Template Management

### `register_custom_template(name: str, template_string: str) -> None`
Registers a new HTML template for global use within the application session.

---
