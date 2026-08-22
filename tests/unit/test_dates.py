from datetime import date, datetime, timezone

import pytest

from src.data.dates import to_jakarta_date


def test_utc_timestamp_normalizes_to_jakarta_same_calendar_day():
    timestamp = datetime(2026, 8, 11, 9, 0, tzinfo=timezone.utc)

    result = to_jakarta_date(timestamp)

    assert result == date(2026, 8, 11)


def test_utc_timestamp_near_midnight_normalizes_to_next_jakarta_day():
    timestamp = datetime(2026, 8, 11, 20, 0, tzinfo=timezone.utc)

    result = to_jakarta_date(timestamp)

    assert result == date(2026, 8, 12)


def test_naive_datetime_preserves_written_calendar_date():
    timestamp = datetime(2026, 8, 11, 23, 30)

    result = to_jakarta_date(timestamp)

    assert result == date(2026, 8, 11)


def test_date_is_returned_unchanged():
    value = date(2026, 8, 11)

    result = to_jakarta_date(value)

    assert result == value


def test_invalid_value_raises_type_error():
    with pytest.raises(TypeError, match="datetime or date"):
        to_jakarta_date("2026-08-11")