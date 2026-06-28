"""Tests for core ExchangeEmailer Calendar/Meeting functionality."""

import datetime
from typing import Any
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from exchangelib import HTMLBody
from exchangelib.items import SEND_ONLY_TO_CHANGED, SEND_TO_ALL_AND_SAVE_COPY

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
    """Test successful update sending to ALL attendees (Default behavior)."""
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
        # send_only_to_changed defaults to False here
    )

    emailer.account.calendar.get.assert_called_once_with(id="existing_id_456")
    assert mock_item.subject == "Updated Sprint Planning"

    # Defaults to sending to everyone
    mock_item.save.assert_called_once_with(send_meeting_invitations=SEND_TO_ALL_AND_SAVE_COPY)
    assert success is True


def test_update_meeting_invite_send_only_to_changed(mock_exchange_connection, sample_config):
    """Test that send_only_to_changed=True forces emails ONLY to changed attendees."""
    emailer = ExchangeEmailer(config=sample_config)
    mock_item = MagicMock()
    mock_item.body = "Original Body"
    emailer.account.calendar.get = MagicMock(return_value=mock_item)

    start_time = datetime.datetime(2026, 6, 26, 10, 0, tzinfo=ZoneInfo("UTC"))
    end_time = datetime.datetime(2026, 6, 26, 11, 0, tzinfo=ZoneInfo("UTC"))

    success = emailer.update_meeting_invite(
        exchange_id="existing_id_456",
        subject="Surgically Updated Sync",
        start=start_time,
        end=end_time,
        send_only_to_changed=True,  # Engaging the flag
    )

    # Assert that it uses the restricted update flag
    mock_item.save.assert_called_once_with(send_meeting_invitations=SEND_ONLY_TO_CHANGED)
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
    end_time = datetime.datetime(2026, 6, 25, 15, 0, tzinfo=ZoneInfo("UTC"))

    with pytest.raises(SendError) as exc_info:
        emailer.update_meeting_invite(
            exchange_id="invalid_id",
            subject="Will Fail",
            start=start_time,
            end=end_time,
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


def test_update_meeting_invite_dispatch_mode_changed(
    mock_exchange_connection: dict[str, Any], sample_config: dict[str, Any]
) -> None:
    """
    Test that the send_only_to_changed toggle correctly evaluates the EWS dispatch mode.

    Args:
        mock_exchange_connection: Fixture containing mocked Exchange endpoints.
        sample_config: Fixture containing valid basic configuration.
    """
    emailer = ExchangeEmailer(config=sample_config)

    # Isolate the in-memory item
    mock_item = MagicMock()
    emailer.account.calendar.get = MagicMock(return_value=mock_item)

    start_time = datetime.datetime(2026, 6, 26, 10, 0, tzinfo=ZoneInfo("UTC"))
    end_time = datetime.datetime(2026, 6, 26, 11, 0, tzinfo=ZoneInfo("UTC"))

    # Execute the update with the new toggle engaged
    success = emailer.update_meeting_invite(
        exchange_id="valid_id_123",
        subject="Surgically Updated Sync",
        start=start_time,
        end=end_time,
        send_only_to_changed=True,
    )

    assert success is True
    # Assert the correct granular flag was passed to the Exchange server using the standard constant
    mock_item.save.assert_called_once_with(send_meeting_invitations=SEND_ONLY_TO_CHANGED)


def test_update_meeting_sets_location(mock_exchange_connection, sample_config):
    """Test that update_meeting_invite applies location when provided."""
    emailer = ExchangeEmailer(config=sample_config)
    mock_item = MagicMock()
    emailer.account.calendar.get = MagicMock(return_value=mock_item)

    t = datetime.datetime(2026, 7, 1, 10, 0, tzinfo=ZoneInfo("UTC"))
    t_end = t + datetime.timedelta(hours=1)  # <-- Architected proper chronology
    emailer.update_meeting_invite(
        exchange_id="abc",
        subject="Meeting",
        start=t,
        end=t_end,  # <-- Use t_end
        location="Room 42",
    )

    assert mock_item.location == "Room 42"


def test_update_meeting_sets_optional_attendees(mock_exchange_connection, sample_config):
    """Test that update_meeting_invite applies optional_attendees when provided."""
    emailer = ExchangeEmailer(config=sample_config)
    mock_item = MagicMock()
    emailer.account.calendar.get = MagicMock(return_value=mock_item)

    t = datetime.datetime(2026, 7, 1, 10, 0, tzinfo=ZoneInfo("UTC"))
    t_end = t + datetime.timedelta(hours=1)  # <-- Architected proper chronology
    emailer.update_meeting_invite(
        exchange_id="abc",
        subject="Meeting",
        start=t,
        end=t_end,  # <-- Use t_end
        optional_attendees=["guest@company.com"],
    )

    assert mock_item.optional_attendees == ["guest@company.com"]


def test_update_meeting_invite_empty_subject_raises_value_error(
    sample_config: dict[str, Any],
) -> None:
    """
    Test that providing an empty or whitespace-only subject fails fast.

    Args:
        sample_config: Fixture containing valid basic configuration.
    """
    emailer = ExchangeEmailer(config=sample_config)

    start_time = datetime.datetime(2026, 6, 26, 10, 0, tzinfo=ZoneInfo("UTC"))
    end_time = datetime.datetime(2026, 6, 26, 11, 0, tzinfo=ZoneInfo("UTC"))

    with pytest.raises(ValueError, match="Meeting subject cannot be empty"):
        emailer.update_meeting_invite(
            exchange_id="valid_id_123",
            subject="   ",  # Defensive check against whitespace bypassing
            start=start_time,
            end=end_time,
        )


def test_update_meeting_invite_invalid_chronology_raises_value_error(
    sample_config: dict[str, Any],
) -> None:
    """
    Test that invalid chronological boundaries (start >= end) are caught locally.

    Args:
        sample_config: Fixture containing valid basic configuration.
    """
    emailer = ExchangeEmailer(config=sample_config)

    start_time = datetime.datetime(2026, 6, 26, 12, 0, tzinfo=ZoneInfo("UTC"))
    end_time = datetime.datetime(2026, 6, 26, 11, 0, tzinfo=ZoneInfo("UTC"))  # 1 hour BEFORE start

    # Scenario A: Start time is after end time
    with pytest.raises(ValueError, match="strictly before the end time"):
        emailer.update_meeting_invite(
            exchange_id="valid_id_123",
            subject="Time Travel Sync",
            start=start_time,
            end=end_time,
        )

    # Scenario B: Start time equals end time (Zero-duration boundary)
    with pytest.raises(ValueError, match="strictly before the end time"):
        emailer.update_meeting_invite(
            exchange_id="valid_id_123",
            subject="Instantaneous Sync",
            start=start_time,
            end=start_time,
        )
