from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.analytics.decision import RiskCategory

_EXECUTION_WINDOW_ROWS = 20

_EXTREME_MIN_AVERAGE_TRADED_VALUE = 250_000_000
_MODERATE_MIN_AVERAGE_TRADED_VALUE = 1_000_000_000

_EXTREME_MAX_ATR_PERCENT = 0.12
_MODERATE_MAX_ATR_PERCENT = 0.07

_MODERATE_MIN_VOLUME_STABILITY = 0.25


@dataclass(frozen=True)
class PublicExecutionRisk:
    """Public OHLCV-based execution-risk classification."""

    category: RiskCategory
    average_traded_value_20d: float | None
    atr_percent: float | None
    zero_volume_days_20d: int | None
    volume_stability_20d: float | None
    reasons: tuple[str, ...]


def classify_public_execution_risk(
    history: pd.DataFrame,
    *,
    atr14: float | None,
    latest_close: float | None,
) -> PublicExecutionRisk:
    """Classify public execution conditions from recent daily OHLCV."""
    required_columns = {"Close", "Volume"}
    if not required_columns.issubset(history.columns):
        return _unknown("Close and Volume are required for execution-risk analysis.")

    if len(history) < _EXECUTION_WINDOW_ROWS:
        return _unknown(
            f"At least {_EXECUTION_WINDOW_ROWS} daily bars are required for "
            "execution-risk analysis."
        )

    if (
        atr14 is None
        or latest_close is None
        or atr14 <= 0
        or latest_close <= 0
    ):
        return _unknown(
            "Usable ATR14 and latest close are required for execution-risk analysis."
        )

    recent = history.tail(_EXECUTION_WINDOW_ROWS).copy()
    close = pd.to_numeric(recent["Close"], errors="coerce")
    volume = pd.to_numeric(recent["Volume"], errors="coerce")

    if close.isna().any() or volume.isna().any():
        return _unknown(
            "Recent Close and Volume values must be complete for execution-risk analysis."
        )

    if (close <= 0).any() or (volume < 0).any():
        return _unknown(
            "Recent Close must be positive and Volume must be non-negative."
        )

    average_traded_value = float((close * volume).mean())
    atr_percent = float(atr14 / latest_close)
    zero_volume_days = int((volume <= 0).sum())
    mean_volume = float(volume.mean())
    median_volume = float(volume.median())

    if mean_volume <= 0:
        return _unknown(
            "Recent average volume must be positive for execution-risk analysis."
        )

    volume_stability = median_volume / mean_volume

    metrics = {
        "average_traded_value_20d": average_traded_value,
        "atr_percent": atr_percent,
        "zero_volume_days_20d": zero_volume_days,
        "volume_stability_20d": volume_stability,
    }

    extreme_reasons = _extreme_reasons(metrics)
    if extreme_reasons:
        return _result(
            category=RiskCategory.EXTREME,
            metrics=metrics,
            reasons=extreme_reasons,
        )

    moderate_reasons = _moderate_reasons(metrics)
    if moderate_reasons:
        return _result(
            category=RiskCategory.MODERATE,
            metrics=metrics,
            reasons=moderate_reasons,
        )

    return _result(
        category=RiskCategory.SAFE,
        metrics=metrics,
        reasons=(
            "Recent public traded value, volatility, and volume stability meet "
            "the current execution-risk thresholds.",
        ),
    )


def _extreme_reasons(metrics: dict[str, float | int]) -> tuple[str, ...]:
    reasons: list[str] = []

    if metrics["zero_volume_days_20d"] > 0:
        reasons.append("Recent 20-day history includes zero-volume bars.")

    if (
        metrics["average_traded_value_20d"]
        < _EXTREME_MIN_AVERAGE_TRADED_VALUE
    ):
        reasons.append(
            "Average 20-day traded value is below IDR 250M."
        )

    if metrics["atr_percent"] > _EXTREME_MAX_ATR_PERCENT:
        reasons.append("ATR14 exceeds 12% of the latest close.")

    return tuple(reasons)


def _moderate_reasons(metrics: dict[str, float | int]) -> tuple[str, ...]:
    reasons: list[str] = []

    if (
        metrics["average_traded_value_20d"]
        < _MODERATE_MIN_AVERAGE_TRADED_VALUE
    ):
        reasons.append(
            "Average 20-day traded value is below IDR 1B."
        )

    if metrics["atr_percent"] > _MODERATE_MAX_ATR_PERCENT:
        reasons.append("ATR14 exceeds 7% of the latest close.")

    if metrics["volume_stability_20d"] < _MODERATE_MIN_VOLUME_STABILITY:
        reasons.append(
            "Recent volume is unstable relative to its average."
        )

    return tuple(reasons)


def _unknown(reason: str) -> PublicExecutionRisk:
    return PublicExecutionRisk(
        category=RiskCategory.UNKNOWN,
        average_traded_value_20d=None,
        atr_percent=None,
        zero_volume_days_20d=None,
        volume_stability_20d=None,
        reasons=(reason,),
    )


def _result(
    *,
    category: RiskCategory,
    metrics: dict[str, float | int],
    reasons: tuple[str, ...],
) -> PublicExecutionRisk:
    return PublicExecutionRisk(
        category=category,
        average_traded_value_20d=float(
            metrics["average_traded_value_20d"]
        ),
        atr_percent=float(metrics["atr_percent"]),
        zero_volume_days_20d=int(metrics["zero_volume_days_20d"]),
        volume_stability_20d=float(metrics["volume_stability_20d"]),
        reasons=reasons,
    )