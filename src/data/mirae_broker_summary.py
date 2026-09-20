from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

from src.domain.broker_summary import (
    BrokerActivity,
    BrokerSummaryMetadata,
    BrokerSummaryResult,
)

_REQUIRED_COLUMNS = (
    "Date",
    "Ticker",
    "Region",
    "Buy_Broker",
    "Buy_Value_IDR",
    "Buy_Average_Price",
    "Sell_Broker",
    "Sell_Value_IDR",
    "Sell_Average_Price",
)
_ALLOWED_REGIONS = {"all", "foreign", "local"}


class MiraeBrokerSummaryError(ValueError):
    """Raised when manual Mirae broker-summary input is invalid."""


def load_mirae_broker_summary(
    path: str | Path,
    *,
    ticker: str,
    start_date: date,
    end_date: date,
    region: str,
) -> BrokerSummaryResult:
    """Load and aggregate detailed manual Mirae broker-summary entries."""
    normalized_ticker = _normalize_ticker(ticker)
    normalized_region = _normalize_region(region)
    _validate_date_range(start_date=start_date, end_date=end_date)

    frame = pd.read_csv(path)
    _validate_columns(frame)

    prepared = _prepare_rows(frame)
    selected = prepared.loc[
        (prepared["Ticker"] == normalized_ticker)
        & (prepared["Region"] == normalized_region)
        & (prepared["Date"] >= pd.Timestamp(start_date))
        & (prepared["Date"] <= pd.Timestamp(end_date))
    ].copy()

    activities = _aggregate_activities(selected)
    metadata = BrokerSummaryMetadata(
        ticker=normalized_ticker,
        start_date=start_date,
        end_date=end_date,
        source="mirae_manual",
        market="RG",
        investor=normalized_region,
    )

    return BrokerSummaryResult(
        metadata=metadata,
        activities=activities,
    )


def _validate_columns(frame: pd.DataFrame) -> None:
    missing_columns = [
        column
        for column in _REQUIRED_COLUMNS
        if column not in frame.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise MiraeBrokerSummaryError(
            "Manual Mirae broker-summary CSV is missing columns: "
            f"{missing}."
        )


def _prepare_rows(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy()
    prepared["Date"] = pd.to_datetime(
        prepared["Date"],
        errors="coerce",
        format="mixed",
    ).dt.normalize()

    if prepared["Date"].isna().any():
        raise MiraeBrokerSummaryError(
            "Manual Mirae broker-summary CSV contains invalid dates."
        )

    prepared["Ticker"] = prepared["Ticker"].map(_normalize_ticker)
    prepared["Region"] = prepared["Region"].map(_normalize_region)

    for column in (
        "Buy_Value_IDR",
        "Buy_Average_Price",
        "Sell_Value_IDR",
        "Sell_Average_Price",
    ):
        prepared[column] = pd.to_numeric(
            prepared[column],
            errors="coerce",
        )

    if prepared[
        [
            "Buy_Value_IDR",
            "Buy_Average_Price",
            "Sell_Value_IDR",
            "Sell_Average_Price",
        ]
    ].isna().any().any():
        raise MiraeBrokerSummaryError(
            "Manual Mirae broker-summary CSV contains missing or "
            "non-numeric value or average-price fields."
        )

    if (
        prepared[
            [
                "Buy_Value_IDR",
                "Buy_Average_Price",
                "Sell_Value_IDR",
                "Sell_Average_Price",
            ]
        ]
        <= 0
    ).any().any():
        raise MiraeBrokerSummaryError(
            "Manual Mirae broker-summary values and average prices "
            "must be positive."
        )

    for column in ("Buy_Broker", "Sell_Broker"):
        prepared[column] = prepared[column].astype(str).str.strip().str.upper()

    if (prepared["Buy_Broker"] == "").any() or (
        prepared["Sell_Broker"] == ""
    ).any():
        raise MiraeBrokerSummaryError(
            "Manual Mirae broker-summary CSV contains blank broker codes."
        )

    return prepared


def _aggregate_activities(
    frame: pd.DataFrame,
) -> tuple[BrokerActivity, ...]:
    aggregates: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "buy_value": 0.0,
            "buy_weighted_price": 0.0,
            "sell_value": 0.0,
            "sell_weighted_price": 0.0,
        }
    )

    for row in frame.itertuples(index=False):
        buy = aggregates[row.Buy_Broker]
        buy["buy_value"] += row.Buy_Value_IDR
        buy["buy_weighted_price"] += (
            row.Buy_Value_IDR * row.Buy_Average_Price
        )

        sell = aggregates[row.Sell_Broker]
        sell["sell_value"] += row.Sell_Value_IDR
        sell["sell_weighted_price"] += (
            row.Sell_Value_IDR * row.Sell_Average_Price
        )

    activities = [
        BrokerActivity(
            broker_code=broker_code,
            buy_frequency=0,
            buy_volume=0,
            buy_value=values["buy_value"],
            sell_frequency=0,
            sell_volume=0,
            sell_value=values["sell_value"],
            buy_average_price=_weighted_average(
                total_value=values["buy_value"],
                weighted_price=values["buy_weighted_price"],
            ),
            sell_average_price=_weighted_average(
                total_value=values["sell_value"],
                weighted_price=values["sell_weighted_price"],
            ),
        )
        for broker_code, values in aggregates.items()
    ]

    return tuple(sorted(activities, key=lambda activity: activity.broker_code))


def _weighted_average(
    *,
    total_value: float,
    weighted_price: float,
) -> float | None:
    if total_value == 0:
        return None

    return weighted_price / total_value


def _normalize_ticker(ticker: object) -> str:
    normalized = str(ticker).strip().upper().replace(".JK", "")
    if not normalized:
        raise MiraeBrokerSummaryError("Ticker must not be blank.")

    return normalized


def _normalize_region(region: object) -> str:
    normalized = str(region).strip().lower()
    if normalized not in _ALLOWED_REGIONS:
        allowed = ", ".join(sorted(_ALLOWED_REGIONS))
        raise MiraeBrokerSummaryError(
            f"Region must be one of: {allowed}."
        )

    return normalized


def _validate_date_range(
    *,
    start_date: date,
    end_date: date,
) -> None:
    if start_date > end_date:
        raise MiraeBrokerSummaryError(
            "start_date must be on or before end_date."
        )