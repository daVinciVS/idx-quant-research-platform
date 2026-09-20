from __future__ import annotations

from collections.abc import Iterable

from src.domain.broker_summary import BrokerActivity


def rank_top_net_buyers(
    activities: Iterable[BrokerActivity],
    *,
    limit: int = 5,
) -> tuple[BrokerActivity, ...]:
    """Return brokers ranked by descending net transaction value."""
    _validate_limit(limit)

    ranked = sorted(
        activities,
        key=lambda activity: (
            activity.net_value,
            activity.net_volume,
            activity.broker_code,
        ),
        reverse=True,
    )

    return tuple(activity for activity in ranked if activity.net_value > 0)[:limit]


def rank_top_net_sellers(
    activities: Iterable[BrokerActivity],
    *,
    limit: int = 5,
) -> tuple[BrokerActivity, ...]:
    """Return brokers ranked by ascending net transaction value."""
    _validate_limit(limit)

    ranked = sorted(
        activities,
        key=lambda activity: (
            activity.net_value,
            activity.net_volume,
            activity.broker_code,
        ),
    )

    return tuple(activity for activity in ranked if activity.net_value < 0)[:limit]


def calculate_price_distance_pct(
    *,
    reference_price: float | None,
    close_price: float | None,
) -> float | None:
    """Return percentage distance from a reference price to the latest close."""
    if reference_price is None or close_price is None:
        return None

    if reference_price <= 0:
        raise ValueError("reference_price must be positive.")

    return ((close_price - reference_price) / reference_price) * 100


def summarize_top_net_buyer_context(
    activities: Iterable[BrokerActivity],
    *,
    close_price: float | None,
) -> str:
    """Return cautious human-readable context for the top net buyer."""
    top_buyers = rank_top_net_buyers(activities, limit=1)

    if not top_buyers:
        return "No net-buying broker activity is available for the selected range."

    top_buyer = top_buyers[0]
    reference_price = top_buyer.buy_average_price
    distance_pct = calculate_price_distance_pct(
        reference_price=reference_price,
        close_price=close_price,
    )

    if reference_price is None or distance_pct is None:
        return (
            f"{top_buyer.broker_code} is the top net buyer over the selected "
            "range, but a comparable weighted buy average is unavailable."
        )

    return (
        f"{top_buyer.broker_code} is the top net buyer over the selected range "
        f"with a weighted buy average of {reference_price:,.2f}. "
        f"The latest close is {distance_pct:+.2f}% relative to that reference. "
        "This is historical broker-flow context, not confirmed support or "
        "resistance."
    )


def _validate_limit(limit: int) -> None:
    if limit < 1:
        raise ValueError("limit must be at least 1.")