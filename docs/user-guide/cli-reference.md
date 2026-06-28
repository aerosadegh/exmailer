# CLI Reference

ExMailer ships with a command-line interface that lets you send emails and calendar invites without writing any Python.

```
exmailer [OPTIONS]
# or
python -m exmailer [OPTIONS]
```

---

## General Options

| Flag | Type | Required | Default | Description |
|---|---|---|---|---|
| `--config PATH` | string | No | — | Path to a JSON or YAML configuration file |
| `--verbose` | flag | No | off | Enable verbose logging output |
| `--log-file PATH` | string | No | `exchange_debug.log` | Destination for verbose debug output (only written when `--verbose` is set) |

---

## Email Content

| Flag | Type | Required | Default | Description |
|---|---|---|---|---|
| `--subject TEXT` | string | **Yes** | — | Email subject line |
| `--body TEXT` | string | No | `""` | Email body. Prefix with `@` to read from a file (e.g. `@body.html`). A warning is printed if the body is empty. |
| `--to EMAIL [EMAIL ...]` | list | **Yes** | — | One or more recipient addresses |
| `--cc EMAIL [EMAIL ...]` | list | No | `[]` | CC recipients |
| `--bcc EMAIL [EMAIL ...]` | list | No | `[]` | BCC recipients (email only — ignored with a warning when `--meeting` is used) |
| `--attachments FILE [FILE ...]` | list | No | `[]` | Files to attach (email only — ignored with a warning when `--meeting` is used). Exits with an error if all specified files are missing. |
| `--importance {Low,Normal,High}` | choice | No | `Normal` | Email priority level (ignored for meeting invites) |

---

## Template Options

`--template` and `--template-file` are **mutually exclusive** — you may only use one at a time.

| Flag | Type | Required | Default | Description |
|---|---|---|---|---|
| `--template {persian,english,minimal,plain,none}` | choice | No | `english` | Built-in template. `persian` = RTL layout; `english` = LTR layout |
| `--template-file PATH` | string | No | — | Path to a custom HTML file. Must contain a `{body}` placeholder |
| `--template-vars JSON` | JSON string | No | `{}` | Extra variables to interpolate into the body, e.g. `'{"date": "1404/11/18"}'`. Must be a JSON **object** (`{...}`); arrays or bare values are rejected. |

---

## Meeting Options

Pass `--meeting` to send a Calendar invite instead of a plain email.
`--start` and `--end` are **required** whenever `--meeting` is used.

| Flag | Type | Required | Default | Description |
|---|---|---|---|---|
| `--meeting` | flag | No | off | Send as a Calendar Meeting Invite |
| `--start "YYYY-MM-DD HH:MM"` | string | With `--meeting` | — | Meeting start time |
| `--end "YYYY-MM-DD HH:MM"` | string | With `--meeting` | — | Meeting end time |
| `--location TEXT` | string | No | `""` | Meeting location |
| `--no-rsvp` | flag | No | off | Suppress RSVP requests to attendees |

> **Note:** `--to` recipients become **required attendees**; `--cc` recipients become **optional attendees** for meeting invites.

---

## Examples

### 1. Basic email

```bash
exmailer \
  --subject "Hello from ExMailer" \
  --body "This is a test email." \
  --to alice@example.com
```

### 1b. High-importance alert with custom log file

```bash
exmailer \
  --subject "CRITICAL: Database unreachable" \
  --body "The main DB is down. Investigating now." \
  --to oncall@example.com \
  --importance High \
  --verbose \
  --log-file /var/log/exmailer_debug.log
```

---

### 2. Email with attachments and CC

```bash
exmailer \
  --subject "Q4 Report" \
  --body "Please find the attached report." \
  --to manager@example.com \
  --cc team@example.com \
  --attachments report.pdf summary.xlsx
```

---

### 3. Email with a custom template file

Your template file must contain a `{body}` placeholder. Any literal `{` or `}` characters inside the HTML (e.g. in `<style>` blocks) must be escaped as `{{` and `}}`.

```bash
exmailer \
  --subject "Newsletter" \
  --body "This month's highlights…" \
  --to subscribers@example.com \
  --template-file /path/to/newsletter.html
```

---

### 4. Email with template variables

Pass a JSON object to `--template-vars`. Keys must match the placeholders used in your template.

```bash
exmailer \
  --subject "Automated Report" \
  --body "Report is ready." \
  --to ops@example.com \
  --template english \
  --template-vars '{"date": "1404/11/18", "department": "Engineering"}'
```

---

### 5. Schedule a meeting invite

```bash
exmailer \
  --meeting \
  --subject "Sprint Planning" \
  --body "Agenda: backlog grooming and sprint goals." \
  --to dev1@example.com dev2@example.com \
  --cc product@example.com \
  --start "2025-02-10 10:00" \
  --end "2025-02-10 11:00" \
  --location "Conference Room A"
```

To send without an RSVP request, add `--no-rsvp`:

```bash
exmailer \
  --meeting \
  --subject "FYI: Team Sync" \
  --body "This is an informational invite." \
  --to team@example.com \
  --start "2025-02-10 14:00" \
  --end "2025-02-10 14:30" \
  --no-rsvp
```

---

### 6. Reading the body from a file

Prefix the path with `@` and ExMailer will read the file contents as the email body. This is useful for HTML bodies or long messages maintained in separate files.

```bash
exmailer \
  --subject "Maintenance Notification" \
  --body @/path/to/notification.html \
  --to all-staff@example.com \
  --template persian
```
