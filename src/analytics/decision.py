from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DecisionLabel(str, Enum):
    CONSIDER_ENTRY = "CONSIDER ENTRY"
    WATCHLIST = "WATCHLIST"
    WAIT = "WAIT / NEUTRAL"
    AVOID = "AVOID"
    INSUFFICIENT_DATA = "INSUFFICIENT DATA"


class RiskCategory(str, Enum):
    SAFE = "SAFE"
    MODERATE = "MODERATE"
    EXTREME = "EXTREME"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DecisionInputs:
    has_sufficient_data: bool
    trend_template_passed: bool
    relative_strength_positive: bool
    wyckoff_phase: str
    extension_risk: bool
    risk_reward_ratio: float | None
    risk_category: RiskCategory = RiskCategory.UNKNOWN


@dataclass(frozen=True)
class TradeDecision:
    label: DecisionLabel
    confidence: str
    reasons: tuple[str, ...]
    next_action: str


def evaluate_trade_decision(inputs: DecisionInputs) -> TradeDecision:
    """Evaluate a deterministic swing-trade decision from validated inputs."""
    if not inputs.has_sufficient_data:
        return TradeDecision(
            label=DecisionLabel.INSUFFICIENT_DATA,
            confidence="Low",
            reasons=("Insufficient validated data for a reliable decision.",),
            next_action="Wait for complete, validated daily OHLCV data.",
        )

    if inputs.risk_category == RiskCategory.EXTREME:
        return TradeDecision(
            label=DecisionLabel.AVOID,
            confidence="Medium",
            reasons=(
                "Extreme risk classification makes execution and risk estimates unreliable.",
            ),
            next_action=(
                "Exclude the ticker until liquidity and volatility are acceptable."
            ),
        )

    reasons: list[str] = []

    if inputs.trend_template_passed:
        reasons.append("Trend template passed.")
    else:
        reasons.append("Trend template did not pass.")

    if inputs.relative_strength_positive:
        reasons.append("Relative strength versus IHSG is positive.")
    else:
        reasons.append("Relative strength versus IHSG is not positive.")

    if inputs.wyckoff_phase:
        reasons.append(f"Wyckoff context: {inputs.wyckoff_phase}.")

    if inputs.extension_risk:
        reasons.append("Price is extended; chasing increases pullback risk.")

    has_acceptable_risk_reward = (
        inputs.risk_reward_ratio is not None
        and inputs.risk_reward_ratio >= 2.0
    )

    if inputs.risk_reward_ratio is not None:
        reasons.append(
            f"Estimated risk/reward ratio: {inputs.risk_reward_ratio:.2f}."
        )

    if inputs.risk_category == RiskCategory.MODERATE:
        reasons.append(
            "Moderate-risk second-liner: require extra liquidity review."
        )

    if inputs.risk_category == RiskCategory.UNKNOWN:
        reasons.append(
            "Risk classification is unavailable; do not promote to entry."
        )

    if inputs.risk_category == RiskCategory.UNKNOWN:
        return TradeDecision(
            label=DecisionLabel.WAIT,
            confidence="Low",
            reasons=tuple(reasons),
            next_action=(
                "Wait until risk classification is available before "
                "considering entry."
            ),
        )

    setup_is_strong = (
        inputs.trend_template_passed
        and inputs.relative_strength_positive
        and not inputs.extension_risk
        and has_acceptable_risk_reward
    )

    if setup_is_strong and inputs.risk_category == RiskCategory.SAFE:
        return TradeDecision(
            label=DecisionLabel.CONSIDER_ENTRY,
            confidence="Medium",
            reasons=tuple(reasons),
            next_action=(
                "Review the planned entry, stop loss, liquidity, and portfolio "
                "risk before placing any order."
            ),
        )

    if (
        setup_is_strong
        and inputs.risk_category == RiskCategory.MODERATE
    ):
        return TradeDecision(
            label=DecisionLabel.WATCHLIST,
            confidence="Medium",
            reasons=tuple(reasons),
            next_action=(
                "Keep on the watchlist. Review liquidity, spread, and position "
                "size before considering entry."
            ),
        )

    if inputs.trend_template_passed and inputs.relative_strength_positive:
        return TradeDecision(
            label=DecisionLabel.WATCHLIST,
            confidence="Medium",
            reasons=tuple(reasons),
            next_action=(
                "Wait for a non-extended entry or improved risk/reward before acting."
            ),
        )

    if not inputs.trend_template_passed and not inputs.relative_strength_positive:
        return TradeDecision(
            label=DecisionLabel.AVOID,
            confidence="Medium",
            reasons=tuple(reasons),
            next_action=(
                "Avoid new long positions until trend and relative strength improve."
            ),
        )

    return TradeDecision(
        label=DecisionLabel.WAIT,
        confidence="Low",
        reasons=tuple(reasons),
        next_action=(
            "Monitor for clearer alignment between trend and relative strength."
        ),
    )