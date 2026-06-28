import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .core import ExchangeEmailer
from .exceptions import ExchangeEmailerError
from .templates import TemplateType, register_custom_template


def _json_dict(s: str) -> dict:
    """argparse type-converter: validates that a JSON string parses to a dict."""
    try:
        value = json.loads(s)
    except json.JSONDecodeError as e:
        raise argparse.ArgumentTypeError(f"Invalid JSON: {e}") from e
    if not isinstance(value, dict):
        raise argparse.ArgumentTypeError(
            '--template-vars must be a JSON object, e.g. \'{"key": "value"}\''
        )
    return value


def parse_datetime(dt_str: str) -> datetime:
    """argparse type-converter: parses 'YYYY-MM-DD HH:MM' into a datetime object."""
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except ValueError:
        raise argparse.ArgumentTypeError(  # noqa: B904
            f"Invalid date format '{dt_str}'. Please use 'YYYY-MM-DD HH:MM'."
        )


def parse_args(args=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Send emails via Microsoft Exchange server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Connection / config
    parser.add_argument("--config", help="Path to configuration file (JSON/YAML)", type=str)
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--log-file",
        default="exchange_debug.log",
        help="Debug log path (only written when --verbose is set)",
    )

    # Template (mutually exclusive group)
    template_group = parser.add_mutually_exclusive_group()
    template_group.add_argument(
        "--template",
        choices=["persian", "english", "minimal", "plain", "none"],
        default="english",
        help="Built-in template to use (persian=RTL, english=LTR)",
    )
    template_group.add_argument(
        "--template-file",
        type=str,
        help="Path to custom HTML template file (must contain {body} placeholder)",
    )

    # Template variables
    parser.add_argument(
        "--template-vars",
        help='Template variables as a JSON object (e.g., \'{"date": "1404/11/18"}\')',
        type=_json_dict,
        default={},
    )

    # Email content
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument(
        "--body",
        required=False,
        help="Email body content (or path to file with @ prefix, e.g., @body.txt)",
    )
    parser.add_argument(
        "--importance",
        choices=["Low", "Normal", "High"],
        default="Normal",
        help="Email priority level (ignored for meeting invites)",
    )

    # Recipients
    parser.add_argument("--to", nargs="+", required=True, help="Recipient email addresses")
    parser.add_argument("--cc", nargs="*", default=[], help="CC recipients")
    parser.add_argument(
        "--bcc", nargs="*", default=[], help="BCC recipients (email only, ignored for meetings)"
    )

    # Attachments
    parser.add_argument(
        "--attachments",
        nargs="*",
        default=[],
        help="Files to attach (email only, not supported for meeting invites)",
    )

    # Calendar/Meeting Options
    meeting_group = parser.add_argument_group("Meeting Options")
    meeting_group.add_argument(
        "--meeting",
        action="store_true",
        help="Send as a Calendar Meeting Invite instead of an Email",
    )
    meeting_group.add_argument(
        "--start",
        type=parse_datetime,
        help="Meeting start time (Format: 'YYYY-MM-DD HH:MM')",
    )
    meeting_group.add_argument(
        "--end",
        type=parse_datetime,
        help="Meeting end time (Format: 'YYYY-MM-DD HH:MM')",
    )
    meeting_group.add_argument("--location", type=str, default="", help="Meeting location")
    meeting_group.add_argument(
        "--no-rsvp", action="store_true", help="Do not request RSVP from attendees"
    )

    return parser.parse_args(args)


def main():
    """Main CLI entry point."""
    args = parse_args()

    # --- 1. Resolve body content ---
    safe_body = args.body or ""
    match safe_body:
        case body_text if body_text.startswith("@"):
            file_path = body_text[1:]
            try:
                with open(file_path, encoding="utf-8") as f:
                    body_content = f.read()
            except Exception as e:
                print(f"❌ Error reading body file '{file_path}': {e!s}", file=sys.stderr)
                sys.exit(1)
        case text:
            body_content = text

    if not body_content and not args.meeting:
        print("⚠️  Warning: Sending email with an empty body.", file=sys.stderr)

    # --- 2. Resolve template ---
    if args.template_file:
        template_path = Path(args.template_file).expanduser().resolve()
        try:
            with open(template_path, encoding="utf-8") as f:
                template_content = f.read()
            if "{body}" not in template_content:
                print(
                    "❌ Template file must contain '{body}' placeholder for content insertion",
                    file=sys.stderr,
                )
                sys.exit(1)
            temp_template_name = f"_cli_temp_{abs(hash(str(template_path)))}"
            register_custom_template(temp_template_name, template_content)
            template: str | TemplateType | None = temp_template_name
            if args.verbose:
                print(f"✅ Loaded custom template from: {template_path}")
        except Exception as e:
            print(f"❌ Error loading template file '{template_path}': {e!s}", file=sys.stderr)
            sys.exit(1)
    else:
        # "plain"/"none" → no wrapper; all other choices are aliases handled by get_template()
        template = None if args.template in ("plain", "none") else args.template

    # --- 3. Resolve and validate attachments ---
    attachments: list[str] = []
    for attachment in args.attachments:
        expanded = Path(attachment).expanduser().resolve()
        if expanded.is_file():
            attachments.append(str(expanded))
        else:
            print(f"⚠️  Warning: Attachment not found: {expanded}", file=sys.stderr)

    if args.attachments and not attachments:
        print(
            "❌ Error: No valid attachment files found. All specified paths are missing or invalid.",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- 4. Pre-flight checks for meetings (before opening any connection) ---
    if args.meeting:
        if not args.start or not args.end:
            print(
                "❌ Error: --start and --end are required when --meeting is used.",
                file=sys.stderr,
            )
            sys.exit(1)
        if attachments:
            print(
                "⚠️  Warning: --attachments are not supported for meeting invites and will be ignored.",
                file=sys.stderr,
            )
        if args.bcc:
            print(
                "⚠️  Warning: --bcc is not supported for meeting invites and will be ignored.",
                file=sys.stderr,
            )

    # --- 5. Connect and send ---
    try:
        with ExchangeEmailer(
            config_path=args.config, verbose=args.verbose, log_file=args.log_file
        ) as emailer:
            if args.meeting:
                exchange_id = emailer.send_meeting_invite(
                    subject=args.subject,
                    start=args.start,
                    end=args.end,
                    body=body_content,
                    required_attendees=args.to,
                    optional_attendees=args.cc,
                    location=args.location,
                    template=template,
                    template_vars=args.template_vars,
                    is_response_requested=not args.no_rsvp,
                )
                if exchange_id:
                    print("✅ Calendar Invite sent successfully!")
                    print(f"   Exchange ID: {exchange_id}")
                    sys.exit(0)
            else:
                success = emailer.send_email(
                    subject=args.subject,
                    body=body_content,
                    recipients=args.to,
                    cc_recipients=args.cc,
                    bcc_recipients=args.bcc,
                    attachments=attachments,
                    template=template,
                    template_vars=args.template_vars,
                    importance=args.importance,
                )
                if success:
                    print("✅ Email sent successfully!")
                    if args.verbose:
                        print(f"   Recipients: {', '.join(args.to)}")
                        if args.cc:
                            print(f"   CC: {', '.join(args.cc)}")
                        if args.bcc:
                            print(f"   BCC: {len(args.bcc)} recipients")
                    sys.exit(0)
                else:
                    print(
                        "❌ Failed to send email (no exception but returned False)",
                        file=sys.stderr,
                    )
                    sys.exit(1)

    except ExchangeEmailerError as e:
        print(f"❌ {type(e).__name__}: {e!s}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e!s}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
