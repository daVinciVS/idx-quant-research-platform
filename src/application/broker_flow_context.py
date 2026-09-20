from __future__ import annotations

from dataclasses import dataclass

from src.application.broker_analytics import (
    calculate_price_distance_pct,
    rank_top_net_buyers,
    rank_top_net_sellers,
)
from src.domain.broker_summary import (
    BrokerActivity,
    BrokerSummaryResult,
)


@dataclass(frozen=True)
class BrokerReference:
    """One broker-flow reference level prepared for presentation."""

    broker_code: str
    net_value: float
    average_price: float | None
    distance_to_close_pct: float | None


@dataclass(frozen=True)
class BrokerFlowContext:
    """Presentation-ready broker-flow context for one research request."""

    ticker: str
    source: str
    start_date: str
    end_date: str
    market: str
    investor: str
    latest_close: float | None
    top_net_buyer: BrokerReference | None
    top_net_seller: BrokerReference | None
    interpretation: str
    caveat: str


_CAVEAT = (
    "Broker-summary activity reflects broker-mediated transactions over the "
    "selected range. It does not identify beneficial owners or confirm future "
    "support, resistance, ownership, or price direction."
)


def build_broker_flow_context(
    result: BrokerSummaryResult,
    *,
    latest_close: float | None,
) -> BrokerFlowContext:
    """Build cautious UI-ready broker-flow context from normalized data."""
    _validate_latest_close(latest_close)

    top_buyers = rank_top_net_buyers(result.activities, limit=1)
    top_sellers = rank_top_net_sellers(result.activities, limit=1)

    top_net_buyer = (
        _build_reference(
            top_buyers[0],
            latest_close=latest_close,
            average_price=top_buyers[0].buy_average_price,
        )
        if top_buyers
        else None
    )
    top_net_seller = (
        _build_reference(
            top_sellers[0],
            latest_close=latest_close,
            average_price=top_sellers[0].sell_average_price,
        )
        if top_sellers
        else None
    )

    return BrokerFlowContext(
        ticker=result.metadata.ticker,
        source=result.metadata.source,
        start_date=result.metadata.start_date.isoformat(),
        end_date=result.metadata.end_date.isoformat(),
        market=result.metadata.market,
        investor=result.metadata.investor,
        latest_close=latest_close,
        top_net_buyer=top_net_buyer,
        top_net_seller=top_net_seller,
        interpretation=_build_interpretation(
            top_net_buyer=top_net_buyer,
            top_net_seller=top_net_seller,
        ),
        caveat=_CAVEAT,
    )


def _build_reference(
    activity: BrokerActivity,
    *,
    latest_close: float | None,
    average_price: float | None,
) -> BrokerReference:
    return BrokerReference(
        broker_code=activity.broker_code,
        net_value=activity.net_value,
        average_price=average_price,
        distance_to_close_pct=calculate_price_distance_pct(
            reference_price=average_price,
            close_price=latest_close,
        ),
    )


def _build_interpretation(
    *,
    top_net_buyer: BrokerReference | None,
    top_net_seller: BrokerReference | None,
) -> str:
    if top_net_buyer is None and top_net_seller is None:
        return (
            "No net buyer or net seller is available for the selected "
            "broker-summary range."
        )

    if top_net_buyer is None:
        return (
            f"{top_net_seller.broker_code} is the top net seller over the "
            "selected range. No net buyer is available."
        )

    if top_net_seller is None:
        return (
            f"{top_net_buyer.broker_code} is the top net buyer over the "
            "selected range. No net seller is available."
        )

    return (
        f"{top_net_buyer.broker_code} is the top net buyer and "
        f"{top_net_seller.broker_code} is the top net seller over the "
        "selected range."
    )


def _validate_latest_close(latest_close: float | None) -> None:
    if latest_close is not None and latest_close <= 0:
        raise ValueError(
            "latest_close must be positive when provided."
        )