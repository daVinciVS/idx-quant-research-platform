import pytest
from src.application.paper_portfolio import (
    PaperPortfolioInputs,
    evaluate_paper_portfolio,
)
from src.application.public_demo import load_demo_case


@pytest.fixture
def inputs() -> PaperPortfolioInputs:
    return PaperPortfolioInputs(
        equity=100_000_000,
        available_cash=50_000_000,
        risk_per_trade_pct=0.0075,
        max_risk_per_trade_pct=0.01,
        max_portfolio_heat_pct=0.04,
        max_position_notional_pct=0.10,
        min_cash_reserve_pct=0.20,
        lot_size=100,
    )


def test_paper_portfolio_sizes_pullback_plan_for_entry_case(inputs):
    evaluation = evaluate_paper_portfolio(
        case=load_demo_case("consider_entry"),
        inputs=inputs,
        plan_type="PULLBACK",
    )

    assert evaluation.eligible is True
    assert evaluation.plan_type == "PULLBACK"
    assert evaluation.result is not None
    assert evaluation.result.action == "ALLOWED"
    assert evaluation.result.quantity == 10_000
    assert evaluation.result.quantity % 100 == 0


def test_paper_portfolio_sizes_breakout_plan_for_entry_case(inputs):
    evaluation = evaluate_paper_portfolio(
        case=load_demo_case("consider_entry"),
        inputs=inputs,
        plan_type="BREAKOUT",
    )

    assert evaluation.eligible is True
    assert evaluation.plan_type == "BREAKOUT"
    assert evaluation.result is not None
    assert evaluation.result.quantity > 0
    assert evaluation.result.quantity % 100 == 0


def test_paper_portfolio_rejects_non_entry_case(inputs):
    evaluation = evaluate_paper_portfolio(
        case=load_demo_case("watchlist"),
        inputs=inputs,
        plan_type="PULLBACK",
    )

    assert evaluation.eligible is False
    assert evaluation.result is None
    assert "CONSIDER ENTRY" in evaluation.message


def test_paper_portfolio_rejects_unknown_plan_type(inputs):
    with pytest.raises(ValueError, match="PULLBACK or BREAKOUT"):
        evaluate_paper_portfolio(
            case=load_demo_case("consider_entry"),
            inputs=inputs,
            plan_type="LIMIT",
        )


def test_paper_portfolio_uses_user_cash_assumption(inputs):
    constrained_inputs = PaperPortfolioInputs(
        **{
            **inputs.__dict__,
            "available_cash": 25_000_000,
        }
    )

    evaluation = evaluate_paper_portfolio(
        case=load_demo_case("consider_entry"),
        inputs=constrained_inputs,
        plan_type="PULLBACK",
    )

    assert evaluation.result is not None
    assert evaluation.result.action == "ALLOWED - REDUCED SIZE"
    assert evaluation.result.quantity == 5_100
    assert "available cash after reserve" in evaluation.result.reasons[0]