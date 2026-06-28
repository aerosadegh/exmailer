"""Tests for CLI interface."""

import datetime
import sys
from unittest.mock import MagicMock, patch

import pytest

from exmailer.cli import _json_dict, main, parse_args, parse_datetime
from exmailer.exceptions import ConfigurationError

# ---------------------------------------------------------------------------
# parse_args — unit tests
# ---------------------------------------------------------------------------


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
    assert args.template == "english"  # Default is now english (LTR)
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


def test_parse_args_persian_template():
    """Test parsing --template persian flag."""
    args = parse_args(
        [
            "--subject",
            "Test",
            "--body",
            "Body",
            "--to",
            "user@company.com",
            "--template",
            "persian",
        ]
    )
    assert args.template == "persian"


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


def test_parse_args_template_vars_non_dict_raises():
    """Test that a JSON array for --template-vars is rejected."""
    with pytest.raises(SystemExit) as exc_info:
        parse_args(
            [
                "--subject",
                "Test",
                "--to",
                "user@company.com",
                "--template-vars",
                '["not", "a", "dict"]',
            ]
        )
    assert exc_info.value.code != 0


def test_parse_args_template_vars_invalid_json_raises():
    """Test that invalid JSON for --template-vars is rejected."""
    with pytest.raises(SystemExit) as exc_info:
        parse_args(
            [
                "--subject",
                "Test",
                "--to",
                "user@company.com",
                "--template-vars",
                "not-valid-json",
            ]
        )
    assert exc_info.value.code != 0


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


def test_parse_args_importance_default():
    """Test that importance defaults to Normal."""
    args = parse_args(["--subject", "Test", "--to", "user@company.com"])
    assert args.importance == "Normal"


def test_parse_args_importance_high():
    """Test parsing --importance High."""
    args = parse_args(
        [
            "--subject",
            "Urgent",
            "--to",
            "user@company.com",
            "--importance",
            "High",
        ]
    )
    assert args.importance == "High"


def test_parse_args_log_file_default():
    """Test that log-file defaults to exchange_debug.log."""
    args = parse_args(["--subject", "Test", "--to", "user@company.com"])
    assert args.log_file == "exchange_debug.log"


def test_parse_args_log_file_custom():
    """Test that a custom --log-file path is parsed correctly."""
    args = parse_args(
        [
            "--subject",
            "Test",
            "--to",
            "user@company.com",
            "--log-file",
            "/var/log/exmailer.log",
        ]
    )
    assert args.log_file == "/var/log/exmailer.log"


def test_cli_missing_required_args():
    """Test CLI exits with error when required args missing."""
    with pytest.raises(SystemExit) as exc_info:
        parse_args([])  # No required --subject or --to
    assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# parse_datetime — unit tests
# ---------------------------------------------------------------------------


def test_parse_datetime_valid():
    """Test successful datetime parsing."""
    result = parse_datetime("2026-06-25 10:00")
    assert result == datetime.datetime(2026, 6, 25, 10, 0)


def test_parse_datetime_invalid_raises():
    """Test that invalid formats raise ArgumentTypeError."""
    import argparse

    with pytest.raises(argparse.ArgumentTypeError):
        parse_datetime("2026/06/25 10:00 PM")


# ---------------------------------------------------------------------------
# _json_dict — unit tests
# ---------------------------------------------------------------------------


def test_json_dict_valid():
    """Test _json_dict with a valid JSON object."""
    result = _json_dict('{"key": "value"}')
    assert result == {"key": "value"}


def test_json_dict_non_dict_raises():
    """Test _json_dict rejects JSON non-objects."""
    import argparse

    with pytest.raises(argparse.ArgumentTypeError, match="JSON object"):
        _json_dict('"just a string"')


def test_json_dict_invalid_json_raises():
    """Test _json_dict rejects malformed JSON."""
    import argparse

    with pytest.raises(argparse.ArgumentTypeError, match="Invalid JSON"):
        _json_dict("not-json{")


# ---------------------------------------------------------------------------
# Meeting arg parsing
# ---------------------------------------------------------------------------


def test_parse_args_meeting_options():
    """Test parsing meeting-specific arguments."""
    args = parse_args(
        [
            "--subject",
            "CLI Meeting Test",
            "--to",
            "team@company.com",
            "--meeting",
            "--start",
            "2026-06-25 10:00",
            "--end",
            "2026-06-25 11:00",
            "--location",
            "Conference Room A",
            "--no-rsvp",
        ]
    )
    assert args.meeting is True
    # --start and --end are now datetime objects (type=parse_datetime)
    assert args.start == datetime.datetime(2026, 6, 25, 10, 0)
    assert args.end == datetime.datetime(2026, 6, 25, 11, 0)
    assert args.location == "Conference Room A"
    assert args.no_rsvp is True


# ---------------------------------------------------------------------------
# main() — integration-style tests (Exchange mocked)
# ---------------------------------------------------------------------------


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
def test_cli_importance_forwarded_to_send_email(mock_emailer_cls):
    """Test that --importance is forwarded to send_email."""
    mock_emailer = MagicMock()
    mock_emailer_cls.return_value.__enter__.return_value = mock_emailer
    mock_emailer.send_email.return_value = True

    test_args = [
        "exmailer",
        "--subject",
        "Urgent Alert",
        "--body",
        "Critical issue.",
        "--to",
        "user@company.com",
        "--importance",
        "High",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 0
    call_kwargs = mock_emailer.send_email.call_args[1]
    assert call_kwargs["importance"] == "High"


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_log_file_forwarded(mock_emailer_cls):
    """Test that --log-file is forwarded to ExchangeEmailer."""
    mock_emailer = MagicMock()
    mock_emailer_cls.return_value.__enter__.return_value = mock_emailer
    mock_emailer.send_email.return_value = True

    test_args = [
        "exmailer",
        "--subject",
        "Test",
        "--body",
        "Body",
        "--to",
        "user@company.com",
        "--verbose",
        "--log-file",
        "my_debug.log",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 0
    mock_emailer_cls.assert_called_once_with(
        config_path=None, verbose=True, log_file="my_debug.log"
    )


# ---------------------------------------------------------------------------
# Body from file
# ---------------------------------------------------------------------------


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_body_from_file_success(mock_emailer_cls, tmp_path):
    """Test successful reading of body content from file using @ prefix."""
    mock_emailer = MagicMock()
    mock_emailer_cls.return_value.__enter__.return_value = mock_emailer
    mock_emailer.send_email.return_value = True

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


@pytest.mark.skipif(sys.platform == "win32", reason="chmod 000 does not prevent reads on Windows")
@patch("exmailer.cli.ExchangeEmailer")
def test_cli_body_from_file_permission_error(mock_emailer_cls, tmp_path):
    """Test error handling for permission denied on body file."""
    body_file = tmp_path / "protected.txt"
    body_file.write_text("secret", encoding="utf-8")
    body_file.chmod(0o000)

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

    body_file.chmod(0o644)


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_body_from_file_invalid_utf8(mock_emailer_cls, tmp_path):
    """Test error handling for non-UTF8 encoded body file."""
    body_file = tmp_path / "invalid_utf8.txt"
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


# ---------------------------------------------------------------------------
# Empty body warning
# ---------------------------------------------------------------------------


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_empty_body_warns(mock_emailer_cls, capsys):
    """Test that a warning is printed when the email body is empty."""
    mock_emailer = MagicMock()
    mock_emailer_cls.return_value.__enter__.return_value = mock_emailer
    mock_emailer.send_email.return_value = True

    test_args = ["exmailer", "--subject", "No Body", "--to", "user@company.com"]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 0
    assert "empty body" in capsys.readouterr().err.lower()


# ---------------------------------------------------------------------------
# Template file
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Attachment edge cases
# ---------------------------------------------------------------------------


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_all_attachments_missing_exits(mock_emailer_cls):
    """Test that exit code 1 when ALL specified attachments are missing."""
    test_args = [
        "exmailer",
        "--subject",
        "Test",
        "--body",
        "Body",
        "--to",
        "user@company.com",
        "--attachments",
        "ghost1.pdf",
        "ghost2.xlsx",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 1
    # Should fail before opening any Exchange connection
    mock_emailer_cls.assert_not_called()


# ---------------------------------------------------------------------------
# Meeting invite flows
# ---------------------------------------------------------------------------


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_meeting_success_flow(mock_emailer_cls):
    """Test successful CLI execution flow for creating a meeting."""
    mock_emailer = MagicMock()
    mock_emailer_cls.return_value.__enter__.return_value = mock_emailer
    mock_emailer.send_meeting_invite.return_value = "mock_exchange_id_999"

    test_args = [
        "exmailer",
        "--subject",
        "Deploy Sync",
        "--to",
        "devops@company.com",
        "--cc",
        "manager@company.com",
        "--meeting",
        "--start",
        "2026-06-25 10:00",
        "--end",
        "2026-06-25 11:00",
        "--location",
        "Virtual",
    ]

    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        mock_emailer.send_meeting_invite.assert_called_once()
        assert not mock_emailer.send_email.called

        call_kwargs = mock_emailer.send_meeting_invite.call_args[1]
        assert call_kwargs["subject"] == "Deploy Sync"
        assert call_kwargs["required_attendees"] == ["devops@company.com"]
        assert call_kwargs["optional_attendees"] == ["manager@company.com"]
        assert call_kwargs["location"] == "Virtual"
        assert call_kwargs["is_response_requested"] is True
        # args.start is already a datetime object after parse_datetime type conversion
        assert isinstance(call_kwargs["start"], datetime.datetime)
        assert call_kwargs["start"].hour == 10


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_meeting_missing_dates(mock_emailer_cls):
    """Test CLI fails gracefully if --meeting is passed without --start or --end."""
    test_args = [
        "exmailer",
        "--subject",
        "Invalid Meeting",
        "--to",
        "user@company.com",
        "--meeting",
        # Missing --start and --end
    ]

    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        # Must fail before the Exchange connection is opened
        mock_emailer_cls.assert_not_called()


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_meeting_invalid_date_format(mock_emailer_cls):
    """Test CLI fails gracefully if the date string is formatted incorrectly."""
    test_args = [
        "exmailer",
        "--subject",
        "Bad Date Format",
        "--to",
        "user@company.com",
        "--meeting",
        "--start",
        "2026/06/25 10:00 PM",  # Invalid format
        "--end",
        "2026-06-25 11:00",
    ]

    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()

        # argparse exits with code 2 for type-conversion errors
        assert exc_info.value.code != 0


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_meeting_warns_on_bcc(mock_emailer_cls, capsys):
    """Test that a warning is printed when --bcc is passed with --meeting."""
    mock_emailer = MagicMock()
    mock_emailer_cls.return_value.__enter__.return_value = mock_emailer
    mock_emailer.send_meeting_invite.return_value = "mock_id"

    test_args = [
        "exmailer",
        "--subject",
        "Team Sync",
        "--to",
        "team@company.com",
        "--bcc",
        "hidden@company.com",
        "--meeting",
        "--start",
        "2026-06-25 10:00",
        "--end",
        "2026-06-25 11:00",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 0
    assert "--bcc is not supported for meeting invites" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Verbose output paths
# ---------------------------------------------------------------------------


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_verbose_template_file_prints_loaded(mock_emailer_cls, tmp_path, capsys):
    """Test that --verbose prints a confirmation when a template file is loaded."""
    mock_emailer = MagicMock()
    mock_emailer_cls.return_value.__enter__.return_value = mock_emailer
    mock_emailer.send_email.return_value = True

    template_file = tmp_path / "t.html"
    template_file.write_text("<html>{body}</html>", encoding="utf-8")

    test_args = [
        "exmailer",
        "--subject",
        "Test",
        "--body",
        "Body",
        "--to",
        "u@c.com",
        "--template-file",
        str(template_file),
        "--verbose",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 0
    assert "Loaded custom template" in capsys.readouterr().out


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_template_file_read_error(mock_emailer_cls, tmp_path):
    """Test exit 1 when the template file cannot be read (e.g. I/O error)."""
    template_file = tmp_path / "t.html"
    template_file.write_text("<html>{body}</html>", encoding="utf-8")

    test_args = [
        "exmailer",
        "--subject",
        "Test",
        "--body",
        "Body",
        "--to",
        "u@c.com",
        "--template-file",
        str(template_file),
    ]
    with patch("builtins.open", side_effect=OSError("disk read error")):
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
    assert exc_info.value.code == 1


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_verbose_shows_cc_and_bcc_counts(mock_emailer_cls, capsys):
    """Test that --verbose prints CC addresses and BCC count after a successful send."""
    mock_emailer = MagicMock()
    mock_emailer_cls.return_value.__enter__.return_value = mock_emailer
    mock_emailer.send_email.return_value = True

    test_args = [
        "exmailer",
        "--subject",
        "Test",
        "--body",
        "Body",
        "--to",
        "to@c.com",
        "--cc",
        "cc@c.com",
        "--bcc",
        "bcc1@c.com",
        "bcc2@c.com",
        "--verbose",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "CC:" in out
    assert "BCC: 2 recipients" in out


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_unexpected_exception_exits_1(mock_emailer_cls):
    """Test that a non-ExchangeEmailerError exception still exits with code 1."""
    mock_emailer = MagicMock()
    mock_emailer_cls.return_value.__enter__.return_value = mock_emailer
    mock_emailer.send_email.side_effect = RuntimeError("something broke internally")

    test_args = [
        "exmailer",
        "--subject",
        "Test",
        "--body",
        "Body",
        "--to",
        "u@c.com",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 1


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_unexpected_exception_verbose_prints_traceback(mock_emailer_cls, capsys):
    """Test that --verbose prints a full traceback on unexpected exceptions."""
    mock_emailer = MagicMock()
    mock_emailer_cls.return_value.__enter__.return_value = mock_emailer
    mock_emailer.send_email.side_effect = RuntimeError("something broke internally")

    test_args = [
        "exmailer",
        "--subject",
        "Test",
        "--body",
        "Body",
        "--to",
        "u@c.com",
        "--verbose",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 1
    assert "RuntimeError" in capsys.readouterr().err


@patch("exmailer.cli.ExchangeEmailer")
def test_cli_meeting_warns_on_attachments(mock_emailer_cls, tmp_path, capsys):
    """Test that a warning is printed when --attachments is passed with --meeting."""
    mock_emailer = MagicMock()
    mock_emailer_cls.return_value.__enter__.return_value = mock_emailer
    mock_emailer.send_meeting_invite.return_value = "mock_id"

    att = tmp_path / "report.pdf"
    att.write_bytes(b"PDF content")

    test_args = [
        "exmailer",
        "--subject",
        "Team Sync",
        "--to",
        "team@company.com",
        "--attachments",
        str(att),
        "--meeting",
        "--start",
        "2026-06-25 10:00",
        "--end",
        "2026-06-25 11:00",
    ]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 0
    assert "--attachments are not supported for meeting invites" in capsys.readouterr().err
