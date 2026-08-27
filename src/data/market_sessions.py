from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, time
from typing import TypeVar
from zoneinfo import ZoneInfo

import pandas as pd

from src.data.dates import to_jakarta_date

JAKARTA_TZ = ZoneInfo("Asia/Jakarta")
IDX_REGULAR_CLOSE = time(16, 0)

T = TypeVar("T")


def is_jakarta_market_open(
    as_of: datetime,
    market_close: time = IDX_REGULAR_CLOSE,
) -> bool:
    """Return whether the Jakarta weekday session is still open."""
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")

    jakarta_time = as_of.astimezone(JAKARTA_TZ)

    if jakarta_time.weekday() >= 5:
        return False

    return jakarta_time.time() < market_close


def exclude_incomplete_daily_bar(
    bars: Iterable[T],
    *,
    as_of: datetime,
    bar_date_getter,
) -> list[T]:
    """Exclude today's daily bar while the Jakarta weekday session is open."""
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")

    bar_list = list(bars)

    if not is_jakarta_market_open(as_of):
        return bar_list

    jakarta_today = to_jakarta_date(as_of)

    return [
        bar
        for bar in bar_list
        if to_jakarta_date(bar_date_getter(bar)) != jakarta_today
    ]


def exclude_incomplete_daily_dataframe(
    history: pd.DataFrame,
    *,
    as_of: datetime,
    date_column: str = "Date",
) -> pd.DataFrame:
    """Return a copy excluding today's incomplete Jakarta daily bar."""
    if date_column not in history.columns:
        raise KeyError(
            f"Expected date column '{date_column}' in history."
        )

    if history.empty:
        return history.copy()

    if not is_jakarta_market_open(as_of):
        return history.copy()

    jakarta_today = pd.Timestamp(to_jakarta_date(as_of))

    return history.loc[
        pd.to_datetime(history[date_column]).dt.normalize()
        != jakarta_today
    ].copy()