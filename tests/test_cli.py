"""Tests for CLI interface."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from exmailer.cli import main, parse_args
from exmailer.exceptions import ConfigurationError


def test_parse_args_basic():
    """Test basic argument parsing."""
    args = parse_args(
        [
            "--subject",
            "Test Subject",
            "--body",
            "Test body",
            "--to",
            "recipient@company.com",
        ]
    )
    assert args.subject == "Test Subject"
    assert args.body == "Test body"
    assert args.to == ["recipient@company.com"]
    assert args.template == "persian"  # Default template
    assert args.template_file is None


def test_parse_args_english_template():
    """Test parsing --template english flag."""
    args = parse_args(
        [
            "--subject",
            "Test",
            "--body",
            "Body",
            "--to",
            "user@company.com",
            "--template",
            "english",
        ]
    )
    assert args.template == "english"


def test_parse_args_template_vars():
    """Test parsing template variables JSON."""
    args = parse_args(
        [
            "--subject",
            "Report",
            "--body",
            "Content",
            "--to",
            "user@company.com",
            "--template-vars",
            '{"date": "1404/11/18", "name": "علی"}',
        ]
    )
    assert args.template_vars == {"date": "1404/11/18", "name": "علی"}


def test_parse_args_attachments():
    """Test parsing multiple attachments."""
    args = parse_args(
        [
            "--subject",
            "With Files",
            "--body",
            "See attachments",
            "--to",
            "user@company.com",
            "--attachments",
            "file1.pdf",
            "file2.xlsx",
        ]
    )
    assert args.attachments == ["file1.pdf", "file2.xlsx"]


def test_cli_missing_required_args():
    """Test CLI exits with error when required args missing."""
    with pytest.raises(SystemExit) as exc_info:
        parse_args([])  # No required --subject or --to
    assert exc_info.value.code != 0


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_success_flow(mock_emailer_cls):
    """Test successful CLI execution flow."""
    mock_emailer = MagicMock()
    mock_emailer_cls.return_value.__enter__.return_value = mock_emailer
    mock_emailer.send_email.return_value = True

    test_args = [
        "exmailer",
        "--subject",
        "CLI Test",
        "--body",
        "Body content",
        "--to",
        "recipient@company.com",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_failure_flow(mock_emailer_cls):
    """Test CLI handles send failures gracefully."""
    mock_emailer = MagicMock()
    mock_emailer_cls.return_value.__enter__.return_value = mock_emailer
    mock_emailer.send_email.return_value = False

    test_args = [
        "exmailer",
        "--subject",
        "Test",
        "--body",
        "Body",
        "--to",
        "user@company.com",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_missing_config_error(mock_emailer_cls):
    """Test CLI handles missing configuration gracefully."""
    mock_emailer_cls.side_effect = ConfigurationError("Missing required configuration fields")

    test_args = [
        "exmailer",
        "--subject",
        "Test",
        "--body",
        "Body",
        "--to",
        "user@company.com",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_body_from_file_success(mock_emailer_cls, tmp_path):
    """Test successful reading of body content from file using @ prefix."""
    mock_emailer = MagicMock()
    mock_emailer_cls.return_value.__enter__.return_value = mock_emailer
    mock_emailer.send_email.return_value = True

    # Create body file with Persian/Unicode content
    body_file = tmp_path / "body.txt"
    body_content = "سلام دنیا! This is a test with Unicode: 你好 🌍"
    body_file.write_text(body_content, encoding="utf-8")

    test_args = [
        "exmailer",
        "--subject",
        "Test",
        "--body",
        f"@{body_file}",
        "--to",
        "user@company.com",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        # Verify body content was passed to send_email
        mock_emailer.send_email.assert_called_once()
        call_kwargs = mock_emailer.send_email.call_args[1]
        assert call_kwargs["body"] == body_content


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_body_from_file_not_found(mock_emailer_cls, tmp_path):
    """Test error handling when body file does not exist."""
    test_args = [
        "exmailer",
        "--subject",
        "Test",
        "--body",
        "@nonexistent.txt",
        "--to",
        "user@company.com",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_body_from_file_permission_error(mock_emailer_cls, tmp_path):
    """Test error handling for permission denied on body file."""
    # Create file then make it unreadable (best effort on Windows)
    body_file = tmp_path / "protected.txt"
    body_file.write_text("secret", encoding="utf-8")

    # Skip on Windows where chmod doesn't work the same way
    if sys.platform != "win32":
        body_file.chmod(0o000)  # Remove all permissions

    test_args = [
        "exmailer",
        "--subject",
        "Test",
        "--body",
        f"@{body_file}",
        "--to",
        "user@company.com",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    # Restore permissions for cleanup if we changed them
    if sys.platform != "win32":
        body_file.chmod(0o644)


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_body_from_file_invalid_utf8(mock_emailer_cls, tmp_path):
    """Test error handling for non-UTF8 encoded body file."""
    body_file = tmp_path / "invalid_utf8.txt"
    # Write Latin-1 encoded content that's invalid UTF-8
    body_file.write_bytes(b"Text with \xff invalid UTF-8 byte")

    test_args = [
        "exmailer",
        "--subject",
        "Test",
        "--body",
        f"@{body_file}",
        "--to",
        "user@company.com",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_custom_template_file(mock_emailer_cls, tmp_path):
    """Test using custom template file via --template-file."""
    mock_emailer = MagicMock()
    mock_emailer_cls.return_value.__enter__.return_value = mock_emailer
    mock_emailer.send_email.return_value = True

    template_file = tmp_path / "custom.html"
    template_file.write_text("<html><body>{body}</body></html>", encoding="utf-8")

    test_args = [
        "exmailer",
        "--subject",
        "Custom Template",
        "--body",
        "Message content",
        "--to",
        "user@company.com",
        "--template-file",
        str(template_file),
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_template_file_missing_placeholder(mock_emailer_cls, tmp_path):
    """Test error when template file lacks {body} placeholder."""
    template_file = tmp_path / "invalid.html"
    template_file.write_text("<html><body>No placeholder</body></html>", encoding="utf-8")

    test_args = [
        "exmailer",
        "--subject",
        "Test",
        "--body",
        "Content",
        "--to",
        "user@company.com",
        "--template-file",
        str(template_file),
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
