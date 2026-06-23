# Command Line Interface (CLI)

ExMailer includes a robust CLI for automation and shell integration.

## Usage
```bash
exmailer [OPTIONS]

```

### General Options

* `--subject`, `-s`: **Required**. Subject of the email or meeting.
* `--body`, `-b`: Content of the email or meeting (can use `@filename.txt` to read from a file).
* `--to`, `-t`: **Required**. Recipient email addresses (Required Attendees for meetings).
* `--cc`: CC recipient addresses (Optional Attendees for meetings).
* `--config`, `-c`: Path to a specific `exmailer.json` or `.yaml` file.
* `--template`: Specify a built-in template (e.g., `persian`, `english`, `none`).

### Meeting Options

* `--meeting`: Flag to send as a Calendar Meeting Invite instead of an Email.
* `--start`: **Required if --meeting**. Start time (Format: `YYYY-MM-DD HH:MM`).
* `--end`: **Required if --meeting**. End time (Format: `YYYY-MM-DD HH:MM`).
* `--location`: Meeting room or virtual location.
* `--no-rsvp`: Flag to not request an Accept/Decline response from attendees.
