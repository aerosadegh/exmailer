

```python

"""
Examples of using ExchangeEmailer with different templates.
"""
from pathlib import Path

from exmailer import ExchangeEmailer, TemplateType, register_custom_template


def example_1_persian_template():
    """Example 1: Using built-in Persian RTL template."""
    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="گزارش هفتگی",
            body="محتوای گزارش هفتگی اینجا قرار می‌گیرد",
            recipients=["colleague@company.com"],
            template=TemplateType.PERSIAN,  # Explicitly use Persian template
        )


def example_2_english_template():
    """Example 2: Using built-in English LTR template."""
    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="Weekly Report",
            body="Weekly report content goes here",
            recipients=["colleague@company.com"],
            template=TemplateType.DEFAULT,  # Use default English template
        )


def example_3_plain_text():
    """Example 3: No template - plain text email."""
    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="Simple Message",
            body="<p>This is plain HTML without any template wrapper</p>",
            recipients=["colleague@company.com"],
            template=None,  # No template
        )


def example_4_template_with_string():
    """Example 4: Using string to specify template."""
    with ExchangeEmailer() as emailer:
        # These are all equivalent ways to get the Persian template
        emailer.send_email(
            subject="تست",
            body="متن پیام",
            recipients=["user@company.com"],
            template="persian",  # String instead of enum
        )

        emailer.send_email(
            subject="تست",
            body="متن پیام",
            recipients=["user@company.com"],
            template=TemplateType.PERSIAN,  # Alternative way
        )



def example_5_custom_template():
    """Example 5: Creating and using a custom template."""

    # Define your custom template
    newsletter_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Georgia, serif;
                background-color: #fafafa;
                padding: 20px;
            }}
            .newsletter {{
                max-width: 700px;
                margin: 0 auto;
                background: white;
                border-left: 5px solid #3498db;
                padding: 40px;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="newsletter">
            <h1>Company Newsletter</h1>
            {body}
            <hr>
            <p style="color: #7f8c8d; font-size: 12px;">
                Unsubscribe | Privacy Policy
            </p>
        </div>
    </body>
    </html>
    """

    # Register the custom template
    register_custom_template("newsletter", newsletter_template)

    # Use the custom template
    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="Monthly Newsletter - January 2026",
            body="""
                <h2>This Month's Highlights</h2>
                <ul>
                    <li>New product launch</li>
                    <li>Team achievements</li>
                    <li>Upcoming events</li>
                </ul>
            """,
            recipients=["team@company.com"],
            template="newsletter",  # Use custom template by name
        )


def example_6_bilingual_email():
    """Example 6: Sending bilingual content with appropriate templates."""

    # Persian version
    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="اعلان مهم",
            body="""
                <h3>اطلاعیه</h3>
                <p>محتوای فارسی در اینجا</p>
            """,
            recipients=["farsi-speakers@company.com"],
            template=TemplateType.PERSIAN,
        )

        # English version
        emailer.send_email(
            subject="Important Announcement",
            body="""
                <h3>Notice</h3>
                <p>English content here</p>
            """,
            recipients=["english-speakers@company.com"],
            template=TemplateType.DEFAULT,
        )


def example_7_template_with_variables():
    """Example 7: Using template variables for dynamic content."""
    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="Daily Report - {date}",
            body="""
                <h3>گزارش روزانه</h3>
                <p>تاریخ: {date}</p>
                <p>کاربر: {username}</p>
                <p>وضعیت: {status}</p>
            """,
            recipients=["manager@company.com"],
            template=TemplateType.PERSIAN,
            template_vars={"date": "1404/11/18", "username": "علی احمدی", "status": "موفق"},
        )


def example_8_corporate_template():
    """Example 8: Professional corporate template."""

    corporate_template = """
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Tahoma', sans-serif;
                direction: rtl;
                margin: 0;
                padding: 0;
                background-color: #f0f0f0;
            }}
            .email-wrapper {{
                max-width: 650px;
                margin: 30px auto;
                background: white;
            }}
            .company-header {{
                background: #1a237e;
                color: white;
                padding: 25px;
                text-align: center;
            }}
            .company-logo {{
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .content-area {{
                padding: 40px 30px;
                line-height: 2;
            }}
            .signature {{
                border-top: 3px solid #1a237e;
                padding: 20px;
                background: #f5f5f5;
                text-align: center;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="company-header">
                <div class="company-logo">شرکت نمونه</div>
                <div>ارتباطات سازمانی</div>
            </div>
            <div class="content-area">
                {body}
            </div>
            <div class="signature">
                <p>این ایمیل از طرف واحد IT ارسال شده است</p>
                <p style="font-size: 11px; margin-top: 10px;">
                    لطفاً به این ایمیل پاسخ ندهید
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    register_custom_template("corporate", corporate_template)

    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="اطلاعیه رسمی شرکت",
            body="""
                <p>با سلام و احترام،</p>
                <p>به اطلاع می‌رساند...</p>
                <br>
                <p>با تشکر</p>
            """,
            recipients=["all@company.com"],
            template="corporate",
        )


def example_9_conditional_template():
    """Example 9: Choosing template based on content language."""

    def send_smart_email(subject: str, body: str, recipients: list):
        """Automatically detect and use appropriate template."""
        # Simple Persian detection (check for Persian characters)
        import re

        has_persian = bool(re.search("[\u0600-\u06ff]", subject + body))

        with ExchangeEmailer() as emailer:
            emailer.send_email(
                subject=subject,
                body=body,
                recipients=recipients,
                template=TemplateType.PERSIAN if has_persian else TemplateType.DEFAULT,
            )

    # Test with Persian content
    send_smart_email(subject="سلام", body="این یک پیام فارسی است", recipients=["user@company.com"])

    # Test with English content
    send_smart_email(
        subject="Hello", body="This is an English message", recipients=["user@company.com"]
    )


def example_10_attachments_and_parameter_flexibility() -> None:
    """
    Example 10: Demonstrating attachment handling and template parameter flexibility.
    
    This example showcases how to attach multiple files using both absolute 
    and relative paths while utilizing different template selection methods 
    (Enum vs. String).
    
    Note:
        Attachments are passed as a list of strings representing file paths.
    """
    # Define file paths using pathlib for cross-platform reliability
    # In a real scenario, ensure these files exist or handle the FileNotFoundError
    report_file: Path = Path("./reports/monthly_stats.pdf")
    log_file: Path = Path("logs/system.log")
    
    # We convert Paths to strings as required by the current exmailer implementation
    attachments: List[str] = [str(report_file), str(log_file)]

    # Option 1: Using TemplateType Enum (Recommended for Type Safety)
    # This approach prevents typos and is easily discoverable via IDE autocomplete.
    with ExchangeEmailer() as emailer:
        try:
            emailer.send_email(
                subject="گزارش نهایی به همراه پیوست",
                body="<p>با سلام، فایل‌های درخواستی به پیوست ارسال شد.</p>",
                recipients=["manager@company.com"],
                template=TemplateType.PERSIAN,  # Explicit RTL Persian template
                attachments=attachments
            )
        except Exception as error:
            print(f"Failed to send email via Enum: {error}")

    # Option 2: Using String Identifier
    # Useful for dynamic template selection from configuration files or databases.
    with ExchangeEmailer() as emailer:
        try:
            emailer.send_email(
                subject="Notification with Attachment",
                body="Please find the logs attached for your review.",
                recipients=["devops@company.com"],
                template="simple",
                attachments=[str(log_file)]
            )
        except Exception as error:
            print(f"Failed to send email via string: {error}")



if __name__ == "__main__":
    # Run examples (comment out as needed)
    example_1_persian_template()
    example_2_english_template()
    example_3_plain_text()
    example_4_template_with_string()
    example_5_custom_template()
    example_6_bilingual_email()
    example_7_template_with_variables()
    example_8_corporate_template()
    example_9_conditional_template()
    example_10_attachments_and_parameter_flexibility()
```
