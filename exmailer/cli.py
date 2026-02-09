import argparse
import json
import os
import sys
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
        required=True,
        help="Email body content (or path to file with @ prefix, e.g., @body.txt)",
    )

    # Recipients
    parser.add_argument("--to", nargs="+", required=True, help="Recipient email addresses")
    parser.add_argument("--cc", nargs="*", default=[], help="CC recipients")
    parser.add_argument("--bcc", nargs="*", default=[], help="BCC recipients")

    # Attachments
    parser.add_argument("--attachments", nargs="*", default=[], help="Files to attach")

    return parser.parse_args(args)


def main():
    """Main CLI entry point."""
    args = parse_args()

    # Handle body content (file or direct text)
    body_content = args.body
    if args.body.startswith("@"):
        file_path = args.body[1:]
        try:
            with open(file_path, encoding="utf-8") as f:
                body_content = f.read()
        except Exception as e:
            print(f"❌ Error reading body file '{file_path}': {e!s}", file=sys.stderr)
            sys.exit(1)

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
        # Use built-in template mapping
        template_map = {
            "persian": TemplateType.PERSIAN,
            "english": TemplateType.DEFAULT,
            "minimal": "minimal",
            "plain": TemplateType.PLAIN,
            "none": TemplateType.PLAIN,
        }
        template = template_map.get(args.template, TemplateType.PERSIAN)

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
                print("❌ Failed to send email (no exception but returned False)", file=sys.stderr)
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
