import pytest
from src.research.backtest_engine import simulate_trade, TradeCostConfig


def test_bullish_trade_calculates_net_return_after_costs():
    trade = simulate_trade(
        signal_score=2,
        entry_price=1000.0,
        exit_price=1050.0,
        cost_config=TradeCostConfig(cost_bps_per_side=20.0),
    )
    assert trade is not None
    assert trade.gross_return_pct == pytest.approx(5.0)
    assert trade.net_return_pct < trade.gross_return_pct


def test_neutral_signal_skips_trade():
    trade = simulate_trade(
        signal_score=0,
        entry_price=1000.0,
        exit_price=1050.0,
        cost_config=TradeCostConfig(),
    )
    assert trade is None