# Command Line Interface (CLI)

ExMailer includes a full-featured CLI for automation, shell scripting, and quick one-off sends.

## Usage

```bash
exmailer [OPTIONS]
# or
python -m exmailer [OPTIONS]
```

---

## Connection & Logging

| Flag | Default | Description |
|---|---|---|
| `--config PATH` | — | Path to a JSON or YAML configuration file |
| `--verbose` | off | Enable verbose debug logging |
| `--log-file PATH` | `exchange_debug.log` | File path for debug output (only written when `--verbose` is set) |

---

## Email Content

| Flag | Required | Default | Description |
|---|---|---|---|
| `--subject TEXT` | **Yes** | — | Email or meeting subject |
| `--body TEXT` | No | `""` | Body content. Prefix with `@` to read from a file (e.g. `@body.html`). A warning is printed when the body is empty. |
| `--to EMAIL [...]` | **Yes** | — | Primary recipients (required attendees for meetings) |
| `--cc EMAIL [...]` | No | `[]` | CC recipients (optional attendees for meetings) |
| `--bcc EMAIL [...]` | No | `[]` | BCC recipients — **email only**; ignored with a warning when `--meeting` is used |
| `--attachments FILE [...]` | No | `[]` | Files to attach — **email only**; ignored with a warning when `--meeting` is used. Exits 1 if all specified files are missing. |
| `--importance {Low,Normal,High}` | No | `Normal` | Email priority level — **email only**; ignored for meeting invites |

---

## Template Options

`--template` and `--template-file` are **mutually exclusive**.

| Flag | Default | Description |
|---|---|---|
| `--template {persian,english,minimal,plain,none}` | `english` | Built-in template: `persian` = RTL, `english` = LTR, `plain`/`none` = no wrapper |
| `--template-file PATH` | — | Path to a custom HTML template file. Must contain a `{body}` placeholder. |
| `--template-vars JSON` | `{}` | Variables to substitute into the body as a JSON **object**, e.g. `'{"date": "1404/11/18"}'`. Bare values or JSON arrays are rejected. |

---

## Meeting Options

Pass `--meeting` to send a Calendar invite instead of a plain email.
`--start` and `--end` are required whenever `--meeting` is used and must use the format `YYYY-MM-DD HH:MM`.

| Flag | Required | Default | Description |
|---|---|---|---|
| `--meeting` | No | off | Send as a Calendar Meeting Invite |
| `--start "YYYY-MM-DD HH:MM"` | With `--meeting` | — | Meeting start time |
| `--end "YYYY-MM-DD HH:MM"` | With `--meeting` | — | Meeting end time |
| `--location TEXT` | No | `""` | Physical or virtual meeting location |
| `--no-rsvp` | No | off | Suppress Accept/Decline RSVP requests |

> **Validation:** `--start` and `--end` are parsed immediately by argparse. An invalid format is caught before any Exchange connection is attempted.

---

## Behaviour Notes

| Situation | Result |
|---|---|
| `--body` is empty (email) | Warning printed to stderr; email is still sent |
| All `--attachments` paths are missing | Error printed, exit code 1 |
| `--attachments` used with `--meeting` | Warning printed; attachments are ignored |
| `--bcc` used with `--meeting` | Warning printed; BCC list is ignored |
| `--template-vars` is not a JSON object | Argparse error, exit code 2 |
| `--start`/`--end` in wrong format | Argparse error, exit code 2 |
| `--meeting` without `--start`/`--end` | Error printed, exit code 1 |
