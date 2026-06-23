import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from .core import ExchangeEmailer
from .exceptions import ExchangeEmailerError
from .templates import TemplateType, register_custom_template


def parse_args(args=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Send emails via Microsoft Exchange server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # Configuration options
    parser.add_argument("--config", help="Path to configuration file (JSON/YAML)", type=str)
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    # Template options (MUTUALLY EXCLUSIVE)
    template_group = parser.add_mutually_exclusive_group()
    template_group.add_argument(
        "--template",
        choices=["persian", "english", "minimal", "plain", "none"],
        default="persian",
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
        help='Template variables as JSON (e.g., \'{"date": "1404/11/18"}\')',
        type=json.loads,
        default={},
    )

    # Email content
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument(
        "--body",
        required=False,
        help="Email body content (or path to file with @ prefix, e.g., @body.txt)",
    )

    # Recipients
    parser.add_argument("--to", nargs="+", required=True, help="Recipient email addresses")
    parser.add_argument("--cc", nargs="*", default=[], help="CC recipients")
    parser.add_argument("--bcc", nargs="*", default=[], help="BCC recipients")

    # Attachments
    parser.add_argument("--attachments", nargs="*", default=[], help="Files to attach")

    # Calendar/Meeting Options
    meeting_group = parser.add_argument_group("Meeting Options")
    meeting_group.add_argument(
        "--meeting",
        action="store_true",
        help="Send as a Calendar Meeting Invite instead of an Email",
    )
    meeting_group.add_argument(
        "--start", type=str, help="Meeting start time (Format: 'YYYY-MM-DD HH:MM')"
    )
    meeting_group.add_argument(
        "--end", type=str, help="Meeting end time (Format: 'YYYY-MM-DD HH:MM')"
    )
    meeting_group.add_argument("--location", type=str, default="", help="Meeting location")
    meeting_group.add_argument(
        "--no-rsvp", action="store_true", help="Do not request responses/RSVP from attendees"
    )

    return parser.parse_args(args)


def parse_datetime(dt_str: str) -> datetime:
    """Helper to parse datetime from CLI string."""
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except ValueError:
        print(
            f"❌ Error: Invalid date format '{dt_str}'. Please use 'YYYY-MM-DD HH:MM'",
            file=sys.stderr,
        )
        sys.exit(1)


def main():
    """Main CLI entry point."""
    args = parse_args()

    safe_body = args.body or ""

    # 1. Handle body content using a match case with a guard clause
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

    # Handle template selection
    template = None
    if args.template_file:
        # Load custom template from file
        template_path = Path(args.template_file).expanduser().resolve()
        try:
            with open(template_path, encoding="utf-8") as f:
                template_content = f.read()

            # Validate template has required placeholder
            if "{body}" not in template_content:
                print(
                    "❌ Template file must contain '{body}' placeholder for content insertion",
                    file=sys.stderr,
                )
                sys.exit(1)

            # Register as temporary custom template
            temp_template_name = f"_cli_temp_{abs(hash(str(template_path)))}"
            register_custom_template(temp_template_name, template_content)
            template = temp_template_name
            if args.verbose:
                print(f"✅ Loaded custom template from: {template_path}")
        except Exception as e:
            print(f"❌ Error loading template file '{template_path}': {e!s}", file=sys.stderr)
            sys.exit(1)
    else:
        # 2. Use match-case instead of dictionary mapping for built-ins
        match args.template:
            case "persian" | "farsi" | "rtl" | "fa":
                template = TemplateType.PERSIAN
            case "default" | "english" | "ltr" | "en":
                template = TemplateType.DEFAULT
            case "minimal" | "simple":
                template = "minimal"
            case "plain" | "none":
                template = TemplateType.PLAIN
            case _:
                # Default fallback if args.template is missing or unrecognized
                template = TemplateType.DEFAULT

    # Process attachments with path expansion
    attachments = []
    for attachment in args.attachments:
        expanded_path = str(Path(attachment).expanduser().resolve())
        if os.path.exists(expanded_path):
            attachments.append(expanded_path)
        else:
            print(f"⚠️  Warning: Attachment not found: {expanded_path}", file=sys.stderr)

    # Send email
    try:
        with ExchangeEmailer(config_path=args.config, verbose=args.verbose) as emailer:
            # 🚀 BRANCH LOGIC: Is it a Meeting or an Email?
            if args.meeting:
                if not args.start or not args.end:
                    print(
                        "❌ Error: --start and --end are required when --meeting is used.",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                start_dt = parse_datetime(args.start)
                end_dt = parse_datetime(args.end)

                exchange_id = emailer.send_meeting_invite(
                    subject=args.subject,
                    start=start_dt,
                    end=end_dt,
                    body=body_content,
                    required_attendees=args.to,
                    optional_attendees=args.cc,
                    location=args.location,
                    template=template,
                    template_vars=args.template_vars,
                    is_response_requested=not args.no_rsvp,  # Flip the flag!
                )

                if exchange_id:
                    print("✅ Calendar Invite sent successfully!")
                    print(f"   Exchange ID: {exchange_id}")  # System admins can copy this ID!
                    sys.exit(0)

            else:
                # Standard Email
                success = emailer.send_email(
                    subject=args.subject,
                    body=body_content,
                    recipients=args.to,
                    cc_recipients=args.cc,
                    bcc_recipients=args.bcc,
                    attachments=attachments,
                    template=template,
                    template_vars=args.template_vars,
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
                        "❌ Failed to send email (no exception but returned False)", file=sys.stderr
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
