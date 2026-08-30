import pytest
from src.analytics.decision import DecisionLabel
from src.application.public_demo import (
    available_demo_cases,
    load_demo_case,
)


def test_public_demo_exposes_expected_cases_in_display_order():
    assert available_demo_cases() == (
        "avoid",
        "watchlist",
        "consider_entry",
        "reduced_size",
        "insufficient_data",
    )


@pytest.mark.parametrize(
    ("case_id", "expected_decision"),
    [
        ("avoid", DecisionLabel.AVOID),
        ("watchlist", DecisionLabel.WATCHLIST),
        ("consider_entry", DecisionLabel.CONSIDER_ENTRY),
        ("reduced_size", DecisionLabel.CONSIDER_ENTRY),
        ("insufficient_data", DecisionLabel.INSUFFICIENT_DATA),
    ],
)
def test_public_demo_cases_use_real_decision_engine(
    case_id,
    expected_decision,
):
    case = load_demo_case(case_id)

    assert case.decision.label == expected_decision
    assert case.ticker.startswith("DEMO-")
    assert case.as_of_date == "2026-08-28"


def test_avoid_case_has_no_trade_plan_or_portfolio_order():
    case = load_demo_case("avoid")

    assert case.trade_plan is None
    assert case.portfolio_result.action == "NOT APPLICABLE"
    assert case.portfolio_result.recommended_quantity == 0


def test_watchlist_case_has_plan_but_no_portfolio_order():
    case = load_demo_case("watchlist")

    assert case.trade_plan is not None
    assert case.portfolio_result.action == "NOT APPLICABLE"
    assert case.portfolio_result.recommended_quantity == 0


def test_consider_entry_case_returns_allowed_lot_sized_order():
    case = load_demo_case("consider_entry")

    assert case.trade_plan is not None
    assert case.portfolio_result.action == "ALLOWED"
    assert case.portfolio_result.recommended_quantity > 0
    assert case.portfolio_result.recommended_quantity % 100 == 0


def test_reduced_size_case_returns_reduced_lot_sized_order():
    case = load_demo_case("reduced_size")

    assert case.trade_plan is not None
    assert case.portfolio_result.action == "ALLOWED - REDUCED SIZE"
    assert case.portfolio_result.recommended_quantity > 0
    assert case.portfolio_result.recommended_quantity % 100 == 0


def test_insufficient_data_case_cannot_receive_a_portfolio_order():
    case = load_demo_case("insufficient_data")

    assert case.trade_plan is None
    assert case.portfolio_result.action == "NOT APPLICABLE"
    assert case.portfolio_result.recommended_quantity == 0


def test_unknown_case_raises_clear_error():
    with pytest.raises(ValueError, match="Unknown demo case"):
        load_demo_case("not-a-real-case")
