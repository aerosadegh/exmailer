"""HTML email templates with flexible template management."""

from enum import StrEnum


class TemplateType(StrEnum):
    """Available email template types."""

    PERSIAN = "persian"  # RTL Persian template
    DEFAULT = "default"  # LTR English template
    PLAIN = "plain"  # No template (plain text)


# Registry for custom templates
_custom_templates: dict[str, str] = {}


def register_custom_template(name: str, template_html: str) -> None:
    """
    Register a custom HTML template.

    Args:
        name: Unique name for the template
        template_html: HTML template string (must contain {body} placeholder)

    Raises:
        ValueError: If template doesn't contain {body} placeholder

    Example:
        >>> my_template = '''
        ... <html>
        ... <body style="font-family: Arial;">
        ...     <div class="content">{body}</div>
        ... </body>
        ... </html>
        ... '''
        >>> register_custom_template("my_newsletter", my_template)
    """
    if "{body}" not in template_html:
        raise ValueError("Template must contain {body} placeholder")

    _custom_templates[name] = template_html


def get_custom_template(name: str) -> str:
    """
    Get a registered custom template.

    Args:
        name: Template name

    Returns:
        Template HTML string

    Raises:
        KeyError: If template not found
    """
    if name not in _custom_templates:
        raise KeyError(
            f"Custom template '{name}' not found. Available: {list(_custom_templates.keys())}"
        )

    return _custom_templates[name]


def list_custom_templates() -> list[str]:
    """Get list of all registered custom template names."""
    return list(_custom_templates.keys())


def get_persian_template() -> str:
    """
    Return Persian (Farsi) RTL email template.

    Returns:
        HTML template string with RTL support
    """
    return """
<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Tahoma', 'Arial', sans-serif;
            direction: rtl;
            text-align: right;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .content {{
            padding: 30px 20px;
            line-height: 1.8;
            color: #333333;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #6c757d;
            border-top: 1px solid #e9ecef;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h2 style="margin: 0;">پیام الکترونیکی</h2>
        </div>
        <div class="content">
            {body}
        </div>
        <div class="footer">
            این پیام به صورت خودکار ارسال شده است
        </div>
    </div>
</body>
</html>
"""


def get_default_template() -> str:
    """
    Return default English LTR email template.

    Returns:
        HTML template string with LTR support
    """
    return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    direction: ltr;
                    text-align: left;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 30px 20px;
                    line-height: 1.6;
                    color: #333333;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #6c757d;
                    border-top: 1px solid #e9ecef;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h2 style="margin: 0;">Email Message</h2>
                </div>
                <div class="content">
                    {body}
                </div>
                <div class="footer">
                    This email was sent automatically
                </div>
            </div>
        </body>
        </html>
        """


def get_minimal_template() -> str:
    """
    Return a minimal template with basic styling.

    Returns:
        Minimal HTML template string
    """
    return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    padding: 20px;
                    color: #333;
                }}
            </style>
        </head>
        <body>
            {body}
        </body>
        </html>
        """


def get_template(template: str | TemplateType) -> str:
    """
    Get template HTML by name or type.

    Args:
        template: Either a TemplateType enum value or a string name of a custom template

    Returns:
        HTML template string

    Raises:
        ValueError: If template type is invalid
        KeyError: If custom template name not found

    Examples:
        >>> # Using enum
        >>> get_template(TemplateType.PERSIAN)

        >>> # Using string for built-in template
        >>> get_template("persian")

        >>> # Using custom template name
        >>> get_template("my_custom_template")
    """
    # Handle TemplateType enum
    match template:
        # Handle TemplateType enum directly
        case TemplateType.PERSIAN:
            return get_persian_template()
        case TemplateType.DEFAULT:
            return get_default_template()
        case TemplateType.PLAIN:
            return "{body}"  # No template

        # Match if it's a string, and bind it to 't_str'
        case str() as t_str:
            # Nested match on the lowercased string using the OR (|) operator
            match t_str.lower():
                case "persian" | "farsi" | "rtl" | "fa":
                    return get_persian_template()
                case "default" | "english" | "ltr" | "en":
                    return get_default_template()
                case "minimal" | "simple":
                    return get_minimal_template()
                case "plain" | "none":
                    return "{body}"
                case _:
                    # Try to get custom template if no built-in matches
                    return get_custom_template(t_str)

        # Fallback for unexpected types
        case _:
            raise ValueError(f"Invalid template type/name: {template}")
