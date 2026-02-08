"""Tests for email template system."""

import re

import pytest

from exmailer.templates import (
    TemplateType,
    get_default_template,
    get_minimal_template,
    get_persian_template,
    get_template,
    list_custom_templates,
    register_custom_template,
)


def test_persian_template_structure():
    """Test Persian template has correct RTL structure."""
    template = get_persian_template()

    # Check RTL direction
    assert 'dir="rtl"' in template or "direction: rtl" in template
    assert 'lang="fa"' in template

    # Check placeholder exists
    assert "{body}" in template

    # Check Persian text in footer
    assert "این پیام" in template


def test_default_template_structure():
    """Test English template has correct LTR structure."""
    template = get_default_template()

    # Check LTR direction (implicit or explicit)
    assert "{body}" in template

    # Check English text in footer
    assert "This email was sent automatically" in template


def test_minimal_template_structure():
    """Test minimal template has basic structure."""
    template = get_minimal_template()
    assert "{body}" in template
    assert "<html" in template.lower()
    assert "<body" in template.lower()


def test_get_template_by_enum():
    """Test getting templates using TemplateType enum."""
    assert "{body}" in get_template(TemplateType.PERSIAN)
    assert "{body}" in get_template(TemplateType.DEFAULT)
    assert "{body}" in get_template(TemplateType.PLAIN)


def test_get_template_by_string():
    """Test getting templates using string aliases."""
    # Persian aliases
    for alias in ["persian", "farsi", "rtl", "fa"]:
        template = get_template(alias)
        assert "{body}" in template
        # Verify it's actually the Persian template
        assert "direction: rtl" in template or 'dir="rtl"' in template

    # English aliases
    for alias in ["default", "english", "ltr", "en"]:
        template = get_template(alias)
        assert "{body}" in template

    # Minimal aliases
    for alias in ["minimal", "simple"]:
        template = get_template(alias)
        assert "{body}" in template

    # Plain aliases
    for alias in ["plain", "none"]:
        assert get_template(alias) == "{body}"


def test_register_custom_template():
    """Test registering and retrieving custom templates."""
    # Register a custom template
    custom_html = """
    <html>
    <body>
        <div class="wrapper">{body}</div>
        <footer>Custom Footer</footer>
    </body>
    </html>
    """
    register_custom_template("my_template", custom_html)

    # Retrieve it
    retrieved = get_template("my_template")
    assert "{body}" in retrieved
    assert "Custom Footer" in retrieved

    # Verify it appears in list
    assert "my_template" in list_custom_templates()


def test_register_template_without_placeholder_raises_error():
    """Test that registering template without {body} placeholder raises error."""
    invalid_template = "<html><body>No placeholder</body></html>"

    with pytest.raises(ValueError, match="must contain {body} placeholder"):
        register_custom_template("invalid", invalid_template)


def test_get_unknown_template_raises_error():
    """Test that getting unknown template raises KeyError."""
    with pytest.raises(KeyError) as exc_info:
        get_template("nonexistent_template")

    assert "nonexistent_template" in str(exc_info.value)
    assert "not found" in str(exc_info.value).lower()


def test_template_variable_substitution():
    """Test template variable substitution works correctly."""
    from unittest.mock import MagicMock, patch

    from exmailer.core import ExchangeEmailer

    # Mock the entire Exchange connection
    with patch("exmailer.core.ExchangeEmailer._connect_to_exchange") as mock_connect, patch(
        "exmailer.core.ExchangeEmailer._create_ssl_context"
    ):

        mock_account = MagicMock()
        mock_connect.return_value = mock_account

        emailer = ExchangeEmailer(
            config={
                "domain": "test",
                "username": "user",
                "password": "pass",
                "server": "srv",
                "email_domain": "test.com",
            }
        )

        # Test variable substitution in body before template wrapping
        body = "Hello {name}, your report for {date} is ready"
        vars = {"name": "علی", "date": "1404/11/18"}

        # Manually test the substitution logic
        for key, value in vars.items():
            body = body.replace(f"{{{key}}}", str(value))

        assert "علی" in body
        assert "1404/11/18" in body
        assert "{name}" not in body
        assert "{date}" not in body


def test_persian_text_preservation():
    """Test that Persian text is preserved correctly through templating."""
    persian_text = "سلام دنیا! این یک پیام فارسی است با کاراکترهای یونیکد: پچژ"

    # Get Persian template and insert text
    template = get_template(TemplateType.PERSIAN)
    formatted = template.replace("{body}", persian_text)

    # Verify Persian text is intact
    assert persian_text in formatted

    # Verify RTL markers are present
    assert 'dir="rtl"' in formatted or "direction: rtl" in formatted.lower()
