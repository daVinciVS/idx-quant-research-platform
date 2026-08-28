import pytest
from src.analytics.decision import RiskCategory
from src.analytics.portfolio_risk import (
    calculate_open_portfolio_heat,
    calculate_position_risk,
    size_proposed_trade,
)
from src.portfolio.models import (
    OpenPosition,
    PortfolioConfig,
    ProposedTrade,
)


@pytest.fixture
def config() -> PortfolioConfig:
    return PortfolioConfig(
        equity=100_000_000,
        available_cash=50_000_000,
        risk_per_trade_pct=0.0075,
        max_risk_per_trade_pct=0.01,
        max_portfolio_heat_pct=0.04,
        max_position_notional_pct=0.10,
        min_cash_reserve_pct=0.20,
        lot_size=100,
    )


@pytest.fixture
def safe_trade() -> ProposedTrade:
    return ProposedTrade(
        ticker="TEST.JK",
        sector="Financials",
        entry_price=1_000,
        stop_price=925,
        target_price=1_200,
        risk_category=RiskCategory.SAFE,
    )


def test_calculate_position_risk_uses_entry_stop_and_quantity():
    position = OpenPosition(
        ticker="BBCA.JK",
        sector="Financials",
        entry_price=9_500,
        stop_price=9_100,
        quantity=500,
        current_price=9_600,
        status="OPEN",
    )

    assert calculate_position_risk(position) == 200_000


def test_open_portfolio_heat_uses_open_positions_only():
    positions = [
        OpenPosition(
            ticker="BBCA.JK",
            sector="Financials",
            entry_price=9_500,
            stop_price=9_100,
            quantity=500,
            current_price=9_600,
            status="OPEN",
        ),
        OpenPosition(
            ticker="ANTM.JK",
            sector="Materials",
            entry_price=3_100,
            stop_price=2_920,
            quantity=1_000,
            current_price=3_150,
            status="CLOSED",
        ),
    ]

    assert calculate_open_portfolio_heat(positions, 100_000_000) == 0.002


def test_safe_trade_is_sized_to_risk_budget_and_lot(config, safe_trade):
    result = size_proposed_trade(config, [], safe_trade)

    assert result.action == "ALLOWED"
    assert result.quantity == 10_000
    assert result.position_value == 10_000_000
    assert result.initial_risk_amount == 750_000
    assert result.initial_risk_pct == 0.0075
    assert result.projected_portfolio_heat_pct == 0.0075


def test_trade_is_reduced_when_cash_reserve_limits_size(config, safe_trade):
    constrained_config = PortfolioConfig(
        **{
            **config.__dict__,
            "available_cash": 25_000_000,
        }
    )

    result = size_proposed_trade(constrained_config, [], safe_trade)

    assert result.action == "ALLOWED — REDUCED SIZE"
    assert result.quantity == 5_000
    assert result.position_value == 5_000_000


def test_trade_is_blocked_when_heat_limit_is_already_reached(config, safe_trade):
    positions = [
        OpenPosition(
            ticker="OPEN.JK",
            sector="Materials",
            entry_price=1_000,
            stop_price=960,
            quantity=100_000,
            current_price=1_000,
            status="OPEN",
        )
    ]

    result = size_proposed_trade(config, positions, safe_trade)

    assert result.action == "BLOCKED — PORTFOLIO HEAT LIMIT"
    assert result.quantity == 0


def test_trade_is_blocked_for_non_safe_risk_category(config, safe_trade):
    proposed = ProposedTrade(
        **{
            **safe_trade.__dict__,
            "risk_category": RiskCategory.MODERATE,
        }
    )

    result = size_proposed_trade(config, [], proposed)

    assert result.action == "BLOCKED — RISK CATEGORY"
    assert result.quantity == 0


def test_trade_is_blocked_when_stop_is_not_below_entry(config, safe_trade):
    proposed = ProposedTrade(
        **{
            **safe_trade.__dict__,
            "stop_price": 1_000,
        }
    )

    result = size_proposed_trade(config, [], proposed)

    assert result.action == "BLOCKED — INVALID TRADE"
    assert result.quantity == 0