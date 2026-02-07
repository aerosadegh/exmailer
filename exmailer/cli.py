import argparse
import json
import os
import sys
from pathlib import Path

from .core import ExchangeEmailer
from .exceptions import ExchangeEmailerError
from .templates import TemplateType


def parse_args(args=None):  # ← Accept optional args parameter
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Send emails via Microsoft Exchange server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Configuration options
    parser.add_argument("--config", help="Path to configuration file (JSON)", type=str)
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    # Email content options
    parser.add_argument(
        "--template",
        choices=["persian", "english", "minimal", "plain", "none"],
        default="persian",
        help="Email template to use (default: persian)",
    )

    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", help="Email body content (or path to file with @ prefix)")
    parser.add_argument(
        "--template-vars",
        help='Template variables in JSON format (e.g., \'{"date": "14/08/1404"}\')',
        type=json.loads,
        default={},
    )

    # Recipients
    parser.add_argument("--to", nargs="+", required=True, help="Recipient email addresses")
    parser.add_argument("--cc", nargs="*", help="CC recipient email addresses", default=[])
    parser.add_argument("--bcc", nargs="*", help="BCC recipient email addresses", default=[])

    # Attachments
    parser.add_argument("--attachments", nargs="*", help="Files to attach", default=[])

    # Language options
    parser.add_argument(
        "--persian",
        action="store_true",
        default=True,
        help="Use Persian RTL template (default)",
    )
    parser.add_argument("--english", action="store_true", help="Use English LTR template")

    return parser.parse_args(args)


def main():
    """Main CLI entry point."""
    args = parse_args()

    # Handle body content (file or direct text)
    body_content = args.body
    if args.body and args.body.startswith("@"):
        file_path = args.body[1:]
        try:
            with open(file_path, encoding="utf-8") as f:
                body_content = f.read()
        except Exception as e:
            print(f"❌ Error reading body file: {str(e)}")
            sys.exit(1)

    # Get attachments with expanded paths
    attachments = []
    for attachment in args.attachments:
        expanded_path = str(Path(attachment).expanduser())
        if os.path.exists(expanded_path):
            attachments.append(expanded_path)
        else:
            print(f"⚠️ Warning: Attachment not found: {expanded_path}")

    try:
        template_map = {
            "persian": TemplateType.PERSIAN,
            "english": TemplateType.DEFAULT,
            "minimal": "minimal",
            "plain": TemplateType.PLAIN,
            "none": TemplateType.PLAIN,
        }
        template = template_map.get(args.template, TemplateType.PERSIAN)

        with ExchangeEmailer(config_path=args.config, verbose=args.verbose) as emailer:
            success = emailer.send_email(
                subject=args.subject,
                body=body_content or "",
                recipients=args.to,
                cc_recipients=args.cc,
                bcc_recipients=args.bcc,
                attachments=attachments,
                template=template,
                template_vars=args.template_vars,
            )

            if success:
                print("✅ Email sent successfully!")
                sys.exit(0)
            else:
                print("❌ Failed to send email")
                sys.exit(1)

    except ExchangeEmailerError as e:
        print(f"❌ {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
