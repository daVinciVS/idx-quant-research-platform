from datetime import date, datetime, time, timezone

import pytest

from src.data.market_sessions import (
    exclude_incomplete_daily_bar,
    is_jakarta_market_open,
)


def test_market_is_open_before_regular_close_on_weekday():
    as_of = datetime(2026, 8, 12, 8, 30, tzinfo=timezone.utc)

    assert is_jakarta_market_open(as_of) is True


def test_market_is_closed_at_regular_close_on_weekday():
    as_of = datetime(2026, 8, 12, 9, 0, tzinfo=timezone.utc)

    assert is_jakarta_market_open(as_of) is False


def test_market_is_closed_on_weekend():
    as_of = datetime(2026, 8, 15, 4, 0, tzinfo=timezone.utc)

    assert is_jakarta_market_open(as_of) is False


def test_naive_as_of_raises_value_error():
    with pytest.raises(ValueError, match="timezone-aware"):
        is_jakarta_market_open(datetime(2026, 8, 12, 15, 0))


def test_incomplete_current_daily_bar_is_excluded_while_market_open():
    bars = [
        {"date": date(2026, 8, 10), "close": 100},
        {"date": date(2026, 8, 11), "close": 101},
        {"date": date(2026, 8, 12), "close": 102},
    ]
    as_of = datetime(2026, 8, 12, 8, 30, tzinfo=timezone.utc)

    result = exclude_incomplete_daily_bar(
        bars,
        as_of=as_of,
        bar_date_getter=lambda bar: bar["date"],
    )

    assert result == bars[:-1]


def test_current_daily_bar_is_retained_after_market_close():
    bars = [
        {"date": date(2026, 8, 11), "close": 101},
        {"date": date(2026, 8, 12), "close": 102},
    ]
    as_of = datetime(2026, 8, 12, 9, 0, tzinfo=timezone.utc)

    result = exclude_incomplete_daily_bar(
        bars,
        as_of=as_of,
        bar_date_getter=lambda bar: bar["date"],
    )

    assert result == bars


def test_current_daily_bar_is_retained_on_weekend():
    bars = [
        {"date": date(2026, 8, 14), "close": 101},
        {"date": date(2026, 8, 15), "close": 102},
    ]
    as_of = datetime(2026, 8, 15, 4, 0, tzinfo=timezone.utc)

    result = exclude_incomplete_daily_bar(
        bars,
        as_of=as_of,
        bar_date_getter=lambda bar: bar["date"],
    )

    assert result == bars