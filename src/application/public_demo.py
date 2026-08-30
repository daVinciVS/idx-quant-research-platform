from __future__ import annotations

from dataclasses import dataclass

from src.analytics.decision import (
    DecisionInputs,
    RiskCategory,
    TradeDecision,
    evaluate_trade_decision,
)
from src.analytics.trade_plan import TradePlan, calculate_trade_plan
from src.portfolio.models import OpenPosition, PortfolioConfig
from src.portfolio.screener_gate import (
    PortfolioContext,
    PortfolioGateResult,
    evaluate_portfolio_gate,
)


@dataclass(frozen=True)
class DemoCase:
    case_id: str
    title: str
    summary: str
    ticker: str
    as_of_date: str
    decision: TradeDecision
    trade_plan: TradePlan | None
    portfolio_result: PortfolioGateResult
    data_status: str


def available_demo_cases() -> tuple[str, ...]:
    """Return stable public demo identifiers in display order."""
    return (
        "avoid",
        "watchlist",
        "consider_entry",
        "reduced_size",
        "insufficient_data",
    )


def load_demo_case(case_id: str) -> DemoCase:
    """Build one deterministic, public-safe product demonstration case."""
    normalized_case_id = case_id.strip().lower()

    if normalized_case_id == "avoid":
        return _avoid_case()
    if normalized_case_id == "watchlist":
        return _watchlist_case()
    if normalized_case_id == "consider_entry":
        return _consider_entry_case()
    if normalized_case_id == "reduced_size":
        return _reduced_size_case()
    if normalized_case_id == "insufficient_data":
        return _insufficient_data_case()

    available = ", ".join(available_demo_cases())
    raise ValueError(f"Unknown demo case: {case_id!r}. Available cases: {available}.")


def _demo_portfolio_context(
    *,
    available_cash: float = 50_000_000,
    positions: list[OpenPosition] | None = None,
) -> PortfolioContext:
    return PortfolioContext(
        config=PortfolioConfig(
            equity=100_000_000,
            available_cash=available_cash,
            risk_per_trade_pct=0.0075,
            max_risk_per_trade_pct=0.01,
            max_portfolio_heat_pct=0.04,
            max_position_notional_pct=0.10,
            min_cash_reserve_pct=0.20,
            lot_size=100,
        ),
        positions=positions or [],
    )


def _portfolio_row(
    *,
    ticker: str,
    decision: TradeDecision,
    screening_status: str,
    risk_classification: str,
    trade_plan: TradePlan | None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "Ticker": ticker,
        "Decision": decision.label.value,
        "Screening Status": screening_status,
        "Risk Classification": risk_classification,
        "Pullback Entry Low": None,
        "Pullback Stop Loss": None,
        "Pullback Target 1": None,
        "Breakout Trigger": None,
        "Breakout Stop Loss": None,
        "Breakout Target 1": None,
    }

    if trade_plan is not None:
        row.update(
            {
                "Pullback Entry Low": trade_plan.pullback_entry_low,
                "Pullback Stop Loss": trade_plan.pullback_stop_loss,
                "Pullback Target 1": trade_plan.pullback_target_1,
                "Breakout Trigger": trade_plan.breakout_entry,
                "Breakout Stop Loss": trade_plan.breakout_stop_loss,
                "Breakout Target 1": trade_plan.breakout_target_1,
            }
        )

    return row


def _not_applicable_portfolio_result(
    decision: TradeDecision,
) -> PortfolioGateResult:
    row = _portfolio_row(
        ticker="DEMO.JK",
        decision=decision,
        screening_status="NO ENTRY PLAN",
        risk_classification="SAFE (Bluechip / Liquid)",
        trade_plan=None,
    )
    return evaluate_portfolio_gate(row, _demo_portfolio_context())


def _avoid_case() -> DemoCase:
    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=True,
            trend_template_passed=False,
            relative_strength_positive=False,
            wyckoff_phase="Distribution Phase D",
            extension_risk=False,
            risk_reward_ratio=1.50,
            risk_category=RiskCategory.SAFE,
        )
    )

    return DemoCase(
        case_id="avoid",
        title="Avoid: weak trend and relative strength",
        summary=(
            "The system declines a new long idea when both the trend template "
            "and relative strength versus IHSG are weak."
        ),
        ticker="DEMO-AVOID.JK",
        as_of_date="2026-08-28",
        decision=decision,
        trade_plan=None,
        portfolio_result=_not_applicable_portfolio_result(decision),
        data_status="Validated demo inputs",
    )


def _watchlist_case() -> DemoCase:
    trade_plan = calculate_trade_plan(
        close=1_000.0,
        atr14=100.0,
        resistance=1_120.0,
        six_month_high=1_250.0,
    )
    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=True,
            trend_template_passed=True,
            relative_strength_positive=True,
            wyckoff_phase="Accumulation Phase D",
            extension_risk=True,
            risk_reward_ratio=trade_plan.pullback_rrr,
            risk_category=RiskCategory.SAFE,
        )
    )

    return DemoCase(
        case_id="watchlist",
        title="Watchlist: valid trend, but price is extended",
        summary=(
            "The setup has positive trend and relative strength evidence, but "
            "the entry is deferred because chasing an extended price increases "
            "pullback risk."
        ),
        ticker="DEMO-WATCH.JK",
        as_of_date="2026-08-28",
        decision=decision,
        trade_plan=trade_plan,
        portfolio_result=_not_applicable_portfolio_result(decision),
        data_status="Validated demo inputs",
    )


def _consider_entry_case() -> DemoCase:
    trade_plan = calculate_trade_plan(
        close=1_000.0,
        atr14=50.0,
        resistance=1_100.0,
        six_month_high=1_200.0,
    )
    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=True,
            trend_template_passed=True,
            relative_strength_positive=True,
            wyckoff_phase="Accumulation Phase D",
            extension_risk=False,
            risk_reward_ratio=trade_plan.pullback_rrr,
            risk_category=RiskCategory.SAFE,
        )
    )
    row = _portfolio_row(
        ticker="DEMO-ENTRY.JK",
        decision=decision,
        screening_status="CONSIDER ENTRY - PULLBACK SETUP",
        risk_classification="SAFE (Bluechip / Liquid)",
        trade_plan=trade_plan,
    )

    return DemoCase(
        case_id="consider_entry",
        title="Consider entry: aligned setup with an executable plan",
        summary=(
            "A safe-category candidate passes the trend, relative-strength, "
            "extension, and risk/reward gates. The paper portfolio then applies "
            "position sizing and board-lot constraints."
        ),
        ticker="DEMO-ENTRY.JK",
        as_of_date="2026-08-28",
        decision=decision,
        trade_plan=trade_plan,
        portfolio_result=evaluate_portfolio_gate(
            row,
            _demo_portfolio_context(),
        ),
        data_status="Validated demo inputs",
    )


def _reduced_size_case() -> DemoCase:
    trade_plan = calculate_trade_plan(
        close=1_000.0,
        atr14=50.0,
        resistance=1_100.0,
        six_month_high=1_200.0,
    )
    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=True,
            trend_template_passed=True,
            relative_strength_positive=True,
            wyckoff_phase="Accumulation Phase D",
            extension_risk=False,
            risk_reward_ratio=trade_plan.breakout_rrr,
            risk_category=RiskCategory.SAFE,
        )
    )
    row = _portfolio_row(
        ticker="DEMO-REDUCED.JK",
        decision=decision,
        screening_status="CONSIDER ENTRY - BREAKOUT SETUP",
        risk_classification="SAFE (Bluechip / Liquid)",
        trade_plan=trade_plan,
    )

    return DemoCase(
        case_id="reduced_size",
        title="Reduced size: portfolio constraints control exposure",
        summary=(
            "The stock-level setup qualifies, but the maximum-position-notional "
            "constraint reduces the order size below the normal risk-budget size."
        ),
        ticker="DEMO-REDUCED.JK",
        as_of_date="2026-08-28",
        decision=decision,
        trade_plan=trade_plan,
        portfolio_result=evaluate_portfolio_gate(
            row,
            _demo_portfolio_context(),
        ),
        data_status="Validated demo inputs",
    )


def _insufficient_data_case() -> DemoCase:
    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=False,
            trend_template_passed=True,
            relative_strength_positive=True,
            wyckoff_phase="Accumulation Phase D",
            extension_risk=False,
            risk_reward_ratio=3.00,
            risk_category=RiskCategory.SAFE,
        )
    )

    return DemoCase(
        case_id="insufficient_data",
        title="Insufficient data: safety gate overrides a positive signal",
        summary=(
            "Even apparently attractive inputs cannot become a trade "
            "recommendation when validated daily market data is incomplete."
        ),
        ticker="DEMO-DATA.JK",
        as_of_date="2026-08-28",
        decision=decision,
        trade_plan=None,
        portfolio_result=_not_applicable_portfolio_result(decision),
        data_status="Insufficient validated data",
    )
