from __future__ import annotations

from dataclasses import dataclass

from src.analytics.decision import DecisionLabel, RiskCategory
from src.analytics.portfolio_risk import size_proposed_trade
from src.application.public_demo import DemoCase
from src.portfolio.models import (
    PortfolioConfig,
    PositionSizeResult,
    ProposedTrade,
)


@dataclass(frozen=True)
class PaperPortfolioInputs:
    equity: float
    available_cash: float
    risk_per_trade_pct: float
    max_risk_per_trade_pct: float
    max_portfolio_heat_pct: float
    max_position_notional_pct: float
    min_cash_reserve_pct: float
    lot_size: int = 100


@dataclass(frozen=True)
class PaperPortfolioEvaluation:
    eligible: bool
    plan_type: str
    result: PositionSizeResult | None
    message: str


def evaluate_paper_portfolio(
    *,
    case: DemoCase,
    inputs: PaperPortfolioInputs,
    plan_type: str,
) -> PaperPortfolioEvaluation:
    """Evaluate a public paper portfolio against an entry-eligible demo case."""
    normalized_plan_type = plan_type.strip().upper()

    if case.decision.label != DecisionLabel.CONSIDER_ENTRY:
        return PaperPortfolioEvaluation(
            eligible=False,
            plan_type=normalized_plan_type,
            result=None,
            message=(
                "Paper sizing is available only when the stock-level decision "
                "is CONSIDER ENTRY."
            ),
        )

    if case.trade_plan is None:
        return PaperPortfolioEvaluation(
            eligible=False,
            plan_type=normalized_plan_type,
            result=None,
            message="The selected case has no valid trade plan to size.",
        )

    if normalized_plan_type not in {"PULLBACK", "BREAKOUT"}:
        raise ValueError("plan_type must be PULLBACK or BREAKOUT")

    config = PortfolioConfig(
        equity=inputs.equity,
        available_cash=inputs.available_cash,
        risk_per_trade_pct=inputs.risk_per_trade_pct,
        max_risk_per_trade_pct=inputs.max_risk_per_trade_pct,
        max_portfolio_heat_pct=inputs.max_portfolio_heat_pct,
        max_position_notional_pct=inputs.max_position_notional_pct,
        min_cash_reserve_pct=inputs.min_cash_reserve_pct,
        lot_size=inputs.lot_size,
    )

    proposed = _proposed_trade_for_plan(
        case=case,
        plan_type=normalized_plan_type,
    )

    result = size_proposed_trade(
        config=config,
        positions=[],
        proposed=proposed,
    )

    return PaperPortfolioEvaluation(
        eligible=True,
        plan_type=normalized_plan_type,
        result=result,
        message=(
            "Paper calculation only. Inputs are not saved and no order is created."
        ),
    )


def _proposed_trade_for_plan(
    *,
    case: DemoCase,
    plan_type: str,
) -> ProposedTrade:
    if case.trade_plan is None:
        raise ValueError("case must include a trade plan")

    if plan_type == "PULLBACK":
        entry_price = case.trade_plan.pullback_entry_low
        stop_price = case.trade_plan.pullback_stop_loss
        target_price = case.trade_plan.pullback_target_1
    else:
        entry_price = case.trade_plan.breakout_entry
        stop_price = case.trade_plan.breakout_stop_loss
        target_price = case.trade_plan.breakout_target_1

    return ProposedTrade(
        ticker=case.ticker,
        sector=None,
        entry_price=entry_price,
        stop_price=stop_price,
        target_price=target_price,
        risk_category=RiskCategory.SAFE,
    )