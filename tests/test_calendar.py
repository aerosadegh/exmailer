"""Tests for core ExchangeEmailer Calendar/Meeting functionality."""

import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from exchangelib import HTMLBody

from exmailer.core import ExchangeEmailer
from exmailer.exceptions import SendError
from exmailer.templates import TemplateType


@pytest.fixture
def mock_calendar_item():
    """Mock the exchangelib CalendarItem class and instance."""
    with patch("exmailer.core.CalendarItem") as mock_cls:
        mock_instance = mock_cls.return_value
        mock_instance.id = "mock_exchange_id_123"
        mock_instance.save = MagicMock()
        mock_instance.delete = MagicMock()
        yield mock_cls, mock_instance


def test_send_meeting_invite_success(mock_exchange_connection, sample_config, mock_calendar_item):
    """Test successful creation of a meeting invite."""
    mock_item_cls, mock_item_instance = mock_calendar_item
    emailer = ExchangeEmailer(config=sample_config)

    start_time = datetime.datetime(2026, 6, 25, 14, 0, tzinfo=ZoneInfo("Asia/Tehran"))
    end_time = datetime.datetime(2026, 6, 25, 15, 0, tzinfo=ZoneInfo("Asia/Tehran"))

    result_id = emailer.send_meeting_invite(
        subject="Sprint Planning",
        start=start_time,
        end=end_time,
        body="<p>Please review the board before the meeting.</p>",
        required_attendees=["team@company.com"],
        optional_attendees=["manager@company.com"],
        location="Room A",
        template=TemplateType.PLAIN,
        is_response_requested=True,
    )

    # Verify CalendarItem was instantiated with correct parameters
    mock_item_cls.assert_called_once()
    _, kwargs = mock_item_cls.call_args
    assert kwargs["subject"] == "Sprint Planning"
    assert kwargs["start"] == start_time
    assert kwargs["end"] == end_time
    assert kwargs["location"] == "Room A"
    assert kwargs["required_attendees"] == ["team@company.com"]
    assert kwargs["optional_attendees"] == ["manager@company.com"]
    assert kwargs["is_response_requested"] is True

    # Body should be wrapped in HTMLBody
    assert isinstance(kwargs["body"], HTMLBody)
    assert "<p>Please review the board before the meeting.</p>" in str(kwargs["body"])

    # Verify save was called correctly
    mock_item_instance.save.assert_called_once_with(send_meeting_invitations="SendToAllAndSaveCopy")

    # Verify the method returns the item.id
    assert result_id == "mock_exchange_id_123"


def test_update_meeting_invite_success(mock_exchange_connection, sample_config):
    """Test successful update of an existing meeting."""
    emailer = ExchangeEmailer(config=sample_config)

    mock_item = MagicMock()
    emailer.account.calendar.get = MagicMock(return_value=mock_item)

    start_time = datetime.datetime(2026, 6, 26, 10, 0, tzinfo=ZoneInfo("Asia/Tehran"))
    end_time = datetime.datetime(2026, 6, 26, 11, 0, tzinfo=ZoneInfo("Asia/Tehran"))

    success = emailer.update_meeting_invite(
        exchange_id="existing_id_456",
        subject="Updated Sprint Planning",
        start=start_time,
        end=end_time,
        body="Time changed.",
        required_attendees=["team@company.com"],
        is_response_requested=False,
    )

    emailer.account.calendar.get.assert_called_once_with(id="existing_id_456")

    # Verify all properties were updated successfully
    assert mock_item.subject == "Updated Sprint Planning"
    assert mock_item.start == start_time
    assert mock_item.end == end_time
    assert mock_item.required_attendees == ["team@company.com"]
    assert mock_item.is_response_requested is False

    # Assert that it uses the safer update flag by default
    mock_item.save.assert_called_once_with(send_meeting_invitations="SendOnlyToChanged")
    assert success is True


def test_update_meeting_invite_force_send_all(mock_exchange_connection, sample_config):
    """Test that force_send_all=True forces emails to everyone and body is safely preserved."""
    emailer = ExchangeEmailer(config=sample_config)
    mock_item = MagicMock()
    # Set a dummy existing body to verify it doesn't get overwritten
    mock_item.body = "Original Body"
    emailer.account.calendar.get = MagicMock(return_value=mock_item)

    start_time = datetime.datetime(2026, 6, 26, 10, 0, tzinfo=ZoneInfo("UTC"))

    success = emailer.update_meeting_invite(
        exchange_id="existing_id_456",
        subject="Forced Update",
        start=start_time,
        end=start_time,
        force_send_all=True,  # Using the new flag
    )

    # Assert the body was preserved because we didn't pass a new one
    assert mock_item.body == "Original Body"

    # Assert that it uses the aggressive update flag
    mock_item.save.assert_called_once_with(send_meeting_invitations="SendToAllAndSaveCopy")
    assert success is True


def test_cancel_meeting_invite_success(mock_exchange_connection, sample_config):
    """Test successful cancellation of a meeting."""
    emailer = ExchangeEmailer(config=sample_config)

    # Mock the retrieved calendar item
    mock_item = MagicMock()
    emailer.account.calendar.get = MagicMock(return_value=mock_item)

    success = emailer.cancel_meeting_invite(exchange_id="existing_id_789")

    # Verify it fetched the correct item
    emailer.account.calendar.get.assert_called_once_with(id="existing_id_789")

    # Verify delete was called with cancellation flag
    mock_item.delete.assert_called_once_with(send_meeting_cancellations="SendToAllAndSaveCopy")
    assert success is True


def test_meeting_timezone_naive_fallback(
    mock_exchange_connection, sample_config, mock_calendar_item
):
    """Test that naive datetimes get a default timezone attached."""
    mock_item_cls, _ = mock_calendar_item
    emailer = ExchangeEmailer(config=sample_config)

    # Intentionally naive datetime (no tzinfo)
    naive_start = datetime.datetime(2026, 6, 25, 14, 0)
    naive_end = datetime.datetime(2026, 6, 25, 15, 0)

    emailer.send_meeting_invite(
        subject="Naive Timezone Test",
        start=naive_start,
        end=naive_end,
    )

    _, kwargs = mock_item_cls.call_args

    # The timezone should have been attached by _ensure_timezone
    assert kwargs["start"].tzinfo is not None
    assert kwargs["end"].tzinfo is not None


def test_send_meeting_failure_raises_send_error(
    mock_exchange_connection, sample_config, mock_calendar_item
):
    """Test that meeting creation failures raise SendError."""
    _, mock_item_instance = mock_calendar_item
    mock_item_instance.save.side_effect = Exception("EWS Server Timeout")

    emailer = ExchangeEmailer(config=sample_config)
    start_time = datetime.datetime(2026, 6, 25, 14, 0, tzinfo=ZoneInfo("UTC"))

    with pytest.raises(SendError) as exc_info:
        emailer.send_meeting_invite(
            subject="Will Fail",
            start=start_time,
            end=start_time,
        )

    assert "EWS Server Timeout" in str(exc_info.value)


def test_update_meeting_failure_raises_send_error(mock_exchange_connection, sample_config):
    """Test that meeting update failures raise SendError."""
    emailer = ExchangeEmailer(config=sample_config)
    emailer.account.calendar.get = MagicMock(side_effect=Exception("Item not found"))

    start_time = datetime.datetime(2026, 6, 25, 14, 0, tzinfo=ZoneInfo("UTC"))

    with pytest.raises(SendError) as exc_info:
        emailer.update_meeting_invite(
            exchange_id="invalid_id",
            subject="Will Fail",
            start=start_time,
            end=start_time,
        )

    assert "Item not found" in str(exc_info.value)


def test_send_meeting_with_template_variables(
    mock_exchange_connection, sample_config, mock_calendar_item
):
    """Test that calendar invites properly utilize the HTML templating engine."""
    mock_item_cls, _ = mock_calendar_item
    emailer = ExchangeEmailer(config=sample_config)

    start_time = datetime.datetime(2026, 6, 25, 14, 0, tzinfo=ZoneInfo("UTC"))

    # Send a meeting using a built-in template and variables
    emailer.send_meeting_invite(
        subject="Template Test",
        start=start_time,
        end=start_time,
        body="Meeting regarding {project_name}",
        template=TemplateType.PERSIAN,
        template_vars={"project_name": "Project Alpha"},
    )

    _, kwargs = mock_item_cls.call_args
    body_str = str(kwargs["body"])

    # 1. Verify the variable was injected
    assert "Project Alpha" in body_str
    # 2. Verify the Persian RTL template was actually applied to the calendar body!
    assert 'dir="rtl"' in body_str or "direction: rtl" in body_str


def test_update_and_cancel_with_empty_id(mock_exchange_connection, sample_config):
    """Test that passing an empty exchange_id gracefully returns False without crashing."""
    emailer = ExchangeEmailer(config=sample_config)
    start_time = datetime.datetime(2026, 6, 25, 14, 0, tzinfo=ZoneInfo("UTC"))

    # Test Update with empty ID
    update_success = emailer.update_meeting_invite(
        exchange_id="",
        subject="Empty ID Update",
        start=start_time,
        end=start_time,
    )

    # Test Cancel with empty ID
    cancel_success = emailer.cancel_meeting_invite(exchange_id="")

    # Both should immediately return False without calling the EWS server
    assert update_success is False
    assert cancel_success is False
    assert not emailer.account.calendar.get.called


def test_cancel_meeting_failure_raises_send_error(mock_exchange_connection, sample_config):
    """Test that cancellation failures (like item already deleted) raise SendError."""
    emailer = ExchangeEmailer(config=sample_config)

    # Mock the get() method to succeed, but the delete() method to fail
    mock_item = MagicMock()
    mock_item.delete.side_effect = Exception("The specified object was not found in the store.")
    emailer.account.calendar.get = MagicMock(return_value=mock_item)

    with pytest.raises(SendError) as exc_info:
        emailer.cancel_meeting_invite(exchange_id="already_deleted_id")

    assert "Failed to cancel meeting" in str(exc_info.value)
    assert "not found in the store" in str(exc_info.value)


def test_domain_rule_chronology_validation(mock_exchange_connection, sample_config):
    """
    DOMAIN RULE: A meeting's end time must strictly be after its start time.
    Exchange will reject this, so we should ensure it raises a SendError.
    """
    emailer = ExchangeEmailer(config=sample_config)

    # Intentionally reverse the times!
    start_time = datetime.datetime(2026, 6, 25, 15, 0, tzinfo=ZoneInfo("Asia/Tehran"))
    end_time = datetime.datetime(
        2026, 6, 25, 14, 0, tzinfo=ZoneInfo("Asia/Tehran")
    )  # 1 hour BEFORE start

    # Mock the EWS server rejecting the reversed times
    mock_item_instance = mock_exchange_connection["message_instance"]
    mock_item_instance.save.side_effect = Exception("ErrorCalendarEndDateIsEarlierThanStartDate")

    with pytest.raises(SendError) as exc_info:
        emailer.send_meeting_invite(
            subject="Time Travel Meeting",
            start=start_time,
            end=end_time,
        )

    assert "Failed to create meeting" in str(exc_info.value)


def test_domain_rule_personal_appointment(
    mock_exchange_connection, sample_config, mock_calendar_item
):
    """
    DOMAIN RULE: A meeting with no attendees is a "Personal Appointment".
    The system must not crash; it should gracefully pass empty lists to EWS.
    """
    mock_item_cls, _ = mock_calendar_item
    emailer = ExchangeEmailer(config=sample_config)

    start_time = datetime.datetime(2026, 6, 25, 14, 0, tzinfo=ZoneInfo("UTC"))

    # Notice: NO attendees provided at all!
    emailer.send_meeting_invite(
        subject="Focus Time (Blocker)",
        start=start_time,
        end=start_time + datetime.timedelta(hours=1),
    )

    _, kwargs = mock_item_cls.call_args

    # Verify the domain handles empty attendees gracefully without crashing
    assert kwargs["required_attendees"] == []
    assert kwargs["optional_attendees"] == []


def test_domain_rule_safe_html_injection(
    mock_exchange_connection, sample_config, mock_calendar_item
):
    """
    DOMAIN RULE: The meeting body must support raw HTML without breaking
    the EWS HTMLBody wrapper, even if the template is None.
    """
    mock_item_cls, _ = mock_calendar_item
    emailer = ExchangeEmailer(config=sample_config)

    start_time = datetime.datetime(2026, 6, 25, 14, 0, tzinfo=ZoneInfo("UTC"))
    complex_html = "<div><h1>Title</h1><p>Description</p></div>"

    emailer.send_meeting_invite(
        subject="HTML Test",
        start=start_time,
        end=start_time,
        body=complex_html,
        template=None,  # Explicitly no template
    )

    _, kwargs = mock_item_cls.call_args

    # Verify the raw HTML was preserved and safely wrapped in the EWS HTMLBody object
    assert isinstance(kwargs["body"], HTMLBody)
    assert complex_html in str(kwargs["body"])
