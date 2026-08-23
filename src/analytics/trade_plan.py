from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class TradePlan:
    pullback_entry_low: float
    pullback_entry_high: float
    pullback_stop_loss: float
    pullback_target_1: float
    pullback_target_2: float
    pullback_rrr: float
    breakout_entry: float
    breakout_stop_loss: float
    breakout_target_1: float
    breakout_target_2: float
    breakout_rrr: float


def calculate_trade_plan(
    *,
    close: float,
    atr14: float,
    resistance: float,
    six_month_high: float,
) -> TradePlan:
    """Create deterministic pullback and breakout swing-trade scenarios."""
    _validate_positive("close", close)
    _validate_positive("atr14", atr14)
    _validate_positive("resistance", resistance)
    _validate_positive("six_month_high", six_month_high)

    pullback_entry_low = max(close - (0.5 * atr14), 0.0)
    pullback_entry_high = close
    pullback_stop_loss = close - (2.0 * atr14)
    pullback_target_1 = max(resistance, close + (1.5 * atr14))
    pullback_target_2 = max(six_month_high, close + (3.0 * atr14))

    pullback_risk = close - pullback_stop_loss
    pullback_reward = pullback_target_2 - close
    pullback_rrr = pullback_reward / pullback_risk

    breakout_entry = resistance
    breakout_stop_loss = breakout_entry - (1.5 * atr14)
    breakout_target_1 = breakout_entry + (1.5 * atr14)
    breakout_target_2 = breakout_entry + (3.0 * atr14)

    breakout_risk = breakout_entry - breakout_stop_loss
    breakout_reward = breakout_target_2 - breakout_entry
    breakout_rrr = breakout_reward / breakout_risk

    return TradePlan(
        pullback_entry_low=pullback_entry_low,
        pullback_entry_high=pullback_entry_high,
        pullback_stop_loss=pullback_stop_loss,
        pullback_target_1=pullback_target_1,
        pullback_target_2=pullback_target_2,
        pullback_rrr=pullback_rrr,
        breakout_entry=breakout_entry,
        breakout_stop_loss=breakout_stop_loss,
        breakout_target_1=breakout_target_1,
        breakout_target_2=breakout_target_2,
        breakout_rrr=breakout_rrr,
    )


def _validate_positive(name: str, value: float) -> None:
    """Reject missing, non-finite, zero, and negative trade-plan inputs."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be a numeric value")

    numeric_value = float(value)

    if not isfinite(numeric_value) or numeric_value <= 0:
        raise ValueError(
            f"{name} must be finite and greater than zero"
        )