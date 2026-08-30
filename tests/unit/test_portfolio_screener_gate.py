import pytest
from src.portfolio.models import OpenPosition, PortfolioConfig
from src.portfolio.screener_gate import (
    PortfolioContext,
    evaluate_portfolio_gate,
)


@pytest.fixture
def context() -> PortfolioContext:
    return PortfolioContext(
        config=PortfolioConfig(
            equity=100_000_000,
            available_cash=50_000_000,
            risk_per_trade_pct=0.0075,
            max_risk_per_trade_pct=0.01,
            max_portfolio_heat_pct=0.04,
            max_position_notional_pct=0.10,
            min_cash_reserve_pct=0.20,
            lot_size=100,
        ),
        positions=[],
    )


@pytest.fixture
def pullback_row() -> dict[str, object]:
    return {
        "Ticker": "TEST.JK",
        "Decision": "CONSIDER ENTRY",
        "Screening Status": "CONSIDER ENTRY - PULLBACK SETUP",
        "Risk Classification": "SAFE (Bluechip / Liquid)",
        "Pullback Entry Low": 1_000,
        "Pullback Stop Loss": 925,
        "Pullback Target 1": 1_200,
        "Breakout Trigger": None,
        "Breakout Stop Loss": None,
        "Breakout Target 1": None,
    }


def test_non_entry_decision_is_not_applicable(context, pullback_row):
    pullback_row["Decision"] = "WATCHLIST"

    result = evaluate_portfolio_gate(pullback_row, context)

    assert result.action == "NOT APPLICABLE"
    assert result.recommended_quantity == 0


def test_entry_is_unavailable_without_portfolio_context(pullback_row):
    result = evaluate_portfolio_gate(pullback_row, None)

    assert result.action == "UNAVAILABLE"
    assert result.recommended_quantity == 0


def test_pullback_entry_is_sized(context, pullback_row):
    result = evaluate_portfolio_gate(pullback_row, context)

    assert result.action == "ALLOWED"
    assert result.plan_type == "PULLBACK"
    assert result.recommended_quantity == 10_000
    assert result.position_value == 10_000_000
    assert result.initial_risk_amount == 750_000


def test_breakout_entry_uses_breakout_plan(context, pullback_row):
    pullback_row["Screening Status"] = "CONSIDER ENTRY - BREAKOUT SETUP"
    pullback_row["Breakout Trigger"] = 1_050
    pullback_row["Breakout Stop Loss"] = 975
    pullback_row["Breakout Target 1"] = 1_250

    result = evaluate_portfolio_gate(pullback_row, context)

    assert result.action == "ALLOWED - REDUCED SIZE"
    assert result.plan_type == "BREAKOUT"
    assert result.recommended_quantity == 9_500
    assert result.position_value == 9_975_000
    assert result.initial_risk_amount == 712_500


def test_review_entry_requires_manual_trade_plan(context, pullback_row):
    pullback_row["Screening Status"] = (
        "CONSIDER ENTRY - REVIEW EXECUTION PLAN"
    )

    result = evaluate_portfolio_gate(pullback_row, context)

    assert result.action == "REVIEW REQUIRED"
    assert result.recommended_quantity == 0


def test_missing_trade_plan_value_blocks_entry(context, pullback_row):
    pullback_row["Pullback Stop Loss"] = None

    result = evaluate_portfolio_gate(pullback_row, context)

    assert result.action == "BLOCKED - INVALID TRADE PLAN"
    assert result.recommended_quantity == 0


def test_non_safe_candidate_is_blocked_by_risk_engine(context, pullback_row):
    pullback_row["Risk Classification"] = (
        "MODERATE RISK (Second Liner)"
    )

    result = evaluate_portfolio_gate(pullback_row, context)

    assert result.action == "BLOCKED - RISK CATEGORY"
    assert result.recommended_quantity == 0


def test_portfolio_heat_limit_blocks_candidate(pullback_row):
    context = PortfolioContext(
        config=PortfolioConfig(
            equity=100_000_000,
            available_cash=50_000_000,
            risk_per_trade_pct=0.0075,
            max_risk_per_trade_pct=0.01,
            max_portfolio_heat_pct=0.04,
            max_position_notional_pct=0.10,
            min_cash_reserve_pct=0.20,
            lot_size=100,
        ),
        positions=[
            OpenPosition(
                ticker="OPEN.JK",
                sector="Materials",
                entry_price=1_000,
                stop_price=960,
                quantity=100_000,
                current_price=1_000,
                status="OPEN",
            )
        ],
    )

    result = evaluate_portfolio_gate(pullback_row, context)

    assert result.action == "BLOCKED - PORTFOLIO HEAT LIMIT"
    assert result.recommended_quantity == 0