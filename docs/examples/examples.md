# Exmailer Documentation & Examples

This guide will walk you through configuring your email client and provide simple, copy-ready examples ranging from basic text emails to advanced dynamic templates.

## 1. Configuration & Initialization

Before sending emails, `exmailer` requires configuration to connect to your Exchange server. You can provide these credentials using either a JSON or YAML file in your project's root directory.

### 1.1. JSON Configuration (`exmailer.json`)
```json
{
  "domain": "your-domain",
  "username": "your-username",
  "password": "your-password",
  "server": "mail.yourcompany.com",
  "email_domain": "yourcompany.com",
  "auth_type": "NTLM",
  "save_copy": true
}
```

### 1.2. YAML Configuration (`exmailer.yaml`)
```yaml
domain: your-domain
username: your-username
password: your-password
server: mail.yourcompany.com
email_domain: yourcompany.com
auth_type: NTLM
save_copy: true
```

---

## 2. Core Messaging

This section covers the absolute basics: sending plain HTML emails without template wrappers, and attaching files to your messages.


```python
"""
Core messaging examples for exmailer: plain text and attachments.
"""
from pathlib import Path
from typing import List

from exmailer import ExchangeEmailer


def send_plain_text_email() -> None:
    """Sends a simple plain HTML email without any built-in template wrapper."""
    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="Simple Message",
            body="<p>This is plain HTML without any template wrapper</p>",
            recipients=["colleague@company.com"],
            template=None,
        )


def send_email_with_attachments() -> None:
    """Demonstrates sending an email with multiple file attachments."""
    # Define file paths using pathlib for cross-platform reliability
    report_file: Path = Path("./reports/monthly_stats.pdf")
    log_file: Path = Path("logs/system.log")
    
    # Convert Paths to strings as required by exmailer
    attachments: List[str] = [str(report_file), str(log_file)]

    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="Notification with Attachment",
            body="<p>Please find the logs attached for your review.</p>",
            recipients=["devops@company.com"],
            template="simple",
            attachments=attachments
        )

if __name__ == "__main__":
    send_plain_text_email()
    send_email_with_attachments()
```


---

## 3. Built-in Templates & Localization

`exmailer` comes with built-in templates optimized for both Left-to-Right (English) and Right-to-Left (Persian) languages. You can select templates using strict Enums or flexible strings.


```python
"""
Examples demonstrating built-in localized templates and selection methods.
"""
from exmailer import ExchangeEmailer, TemplateType


def send_english_ltr_template() -> None:
    """Sends an email using the default Left-to-Right English template."""
    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="Weekly Report",
            body="<p>Weekly report content goes here</p>",
            recipients=["colleague@company.com"],
            template=TemplateType.DEFAULT,
        )


def send_persian_rtl_template() -> None:
    """Sends an email using the Right-to-Left Persian template."""
    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="گزارش هفتگی",
            body="<p>محتوای گزارش هفتگی اینجا قرار می‌گیرد</p>",
            recipients=["colleague@company.com"],
            template=TemplateType.PERSIAN,
        )


def send_template_via_string_identifier() -> None:
    """Demonstrates selecting a template using a string rather than an Enum."""
    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="تست",
            body="<p>متن پیام</p>",
            recipients=["user@company.com"],
            template="persian", 
        )

if __name__ == "__main__":
    send_english_ltr_template()
    send_persian_rtl_template()
    send_template_via_string_identifier()
```


---

## 4. Advanced Templating

For production environments, you will often need dynamic data injection and custom-branded HTML layouts.


```python
"""
Advanced templating: Dynamic variables and custom HTML registration.
"""
from exmailer import ExchangeEmailer, TemplateType, register_custom_template


def send_email_with_dynamic_variables() -> None:
    """Injects dynamic data into a template using the template_vars parameter."""
    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="Daily Report",
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


def register_and_send_custom_newsletter() -> None:
    """Creates, registers, and uses a custom HTML newsletter template."""
    newsletter_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Georgia, serif; background-color: #fafafa; padding: 20px; }
            .newsletter { max-width: 700px; margin: 0 auto; background: white; border-left: 5px solid #3498db; padding: 40px; }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        </style>
    </head>
    <body>
        <div class="newsletter">
            <h1>Company Newsletter</h1>
            {body}
            <hr>
            <p style="color: #7f8c8d; font-size: 12px;">Unsubscribe | Privacy Policy</p>
        </div>
    </body>
    </html>
    """

    register_custom_template("newsletter", newsletter_html)

    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="Monthly Newsletter - January 2026",
            body="<ul><li>New product launch</li><li>Team achievements</li></ul>",
            recipients=["team@company.com"],
            template="newsletter",
        )


def register_and_send_corporate_announcement() -> None:
    """Registers and uses a formal, RTL corporate layout."""
    corporate_html = """
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <style>
            body { font-family: 'Tahoma', sans-serif; direction: rtl; background-color: #f0f0f0; }
            .email-wrapper { max-width: 650px; margin: 30px auto; background: white; }
            .company-header { background: #1a237e; color: white; padding: 25px; text-align: center; }
            .content-area { padding: 40px 30px; line-height: 2; }
            .signature { border-top: 3px solid #1a237e; padding: 20px; background: #f5f5f5; text-align: center; color: #666; }
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="company-header">شرکت نمونه</div>
            <div class="content-area">{body}</div>
            <div class="signature"><p>این ایمیل از طرف واحد IT ارسال شده است</p></div>
        </div>
    </body>
    </html>
    """

    register_custom_template("corporate", corporate_html)

    with ExchangeEmailer() as emailer:
        emailer.send_email(
            subject="اطلاعیه رسمی شرکت",
            body="<p>با سلام و احترام، به اطلاع می‌رساند...</p>",
            recipients=["all@company.com"],
            template="corporate",
        )

if __name__ == "__main__":
    send_email_with_dynamic_variables()
    register_and_send_custom_newsletter()
    register_and_send_corporate_announcement()
```

---

## 5. Dynamic & Smart Routing

When handling multi-lingual systems, you can route content to different templates manually, or write wrappers to detect the language automatically.


```python
"""
Smart routing: Bilingual dispatch and automatic language detection.
"""
import re
from exmailer import ExchangeEmailer, TemplateType

# Pre-compile regex for performance
PERSIAN_CHAR_PATTERN = re.compile(r"[\u0600-\u06ff]")


def send_bilingual_notification() -> None:
    """Sends identical announcements to different audiences using respective templates."""
    with ExchangeEmailer() as emailer:
        # Persian version
        emailer.send_email(
            subject="اعلان مهم",
            body="<p>محتوای فارسی در اینجا</p>",
            recipients=["farsi-speakers@company.com"],
            template=TemplateType.PERSIAN,
        )

        # English version
        emailer.send_email(
            subject="Important Announcement",
            body="<p>English content here</p>",
            recipients=["english-speakers@company.com"],
            template=TemplateType.DEFAULT,
        )


def send_auto_detected_language_email() -> None:
    """Automatically detects Persian characters and routes to the correct template."""
    
    def _smart_dispatch(subject: str, body: str, recipients: list) -> None:
        """Internal helper to detect language and send."""
        has_persian = bool(PERSIAN_CHAR_PATTERN.search(subject + body))
        selected_template = TemplateType.PERSIAN if has_persian else TemplateType.DEFAULT

        with ExchangeEmailer() as emailer:
            emailer.send_email(
                subject=subject,
                body=body,
                recipients=recipients,
                template=selected_template,
            )

    # Dispatching test emails
    _smart_dispatch(
        subject="سلام", 
        body="این یک پیام فارسی است", 
        recipients=["user@company.com"]
    )
    
    _smart_dispatch(
        subject="Hello", 
        body="This is an English message", 
        recipients=["user@company.com"]
    )

if __name__ == "__main__":
    send_bilingual_notification()
    send_auto_detected_language_email()
```