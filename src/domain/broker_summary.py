from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class BrokerActivity:
    """One broker's aggregated activity across a selected date range."""

    broker_code: str
    buy_frequency: int
    buy_volume: int
    buy_value: float
    sell_frequency: int
    sell_volume: int
    sell_value: float
    buy_average_price: float | None
    sell_average_price: float | None

    @property
    def net_volume(self) -> int:
        """Return bought volume less sold volume."""
        return self.buy_volume - self.sell_volume

    @property
    def net_value(self) -> float:
        """Return bought value less sold value."""
        return self.buy_value - self.sell_value


@dataclass(frozen=True)
class BrokerSummaryMetadata:
    """Source and scope metadata for a broker-summary request."""

    ticker: str
    start_date: date
    end_date: date
    source: str
    market: str
    investor: str

@dataclass(frozen=True)
class BrokerSummaryResult:
    """Normalized broker-summary data with request metadata."""

    metadata: BrokerSummaryMetadata
    activities: tuple[BrokerActivity, ...]