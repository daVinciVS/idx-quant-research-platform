from __future__ import annotations

from datetime import date, datetime
from typing import Union
from zoneinfo import ZoneInfo

JAKARTA_TZ = ZoneInfo("Asia/Jakarta")

DateLike = Union[datetime, date]


def to_jakarta_date(value: DateLike) -> date:
    """Return the Asia/Jakarta calendar date for a date or datetime value."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.date()
        return value.astimezone(JAKARTA_TZ).date()

    if isinstance(value, date):
        return value

    raise TypeError("value must be a datetime or date")