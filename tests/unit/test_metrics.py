import pytest
from src.research.metrics import (
    annualized_volatility,
    cagr,
    max_drawdown,
    sharpe_ratio,
    win_rate,
)


def test_cagr_doubles_over_one_year():
    result = cagr(cumulative_return_pct=100.0, num_days=365)
    assert result == pytest.approx(100.0, rel=0.01)


def test_cagr_handles_two_year_growth():
    result = cagr(cumulative_return_pct=100.0, num_days=730)
    assert result == pytest.approx(41.4, rel=0.02)


def test_max_drawdown_detects_peak_to_trough_decline():
    equity_curve = [100, 120, 90, 110]
    result = max_drawdown(equity_curve)
    assert result == pytest.approx(-25.0, rel=0.01)


def test_win_rate_calculates_percentage_of_profitable_trades():
    trade_returns = [5.0, -2.0, 3.0, -1.0]
    result = win_rate(trade_returns)
    assert result == pytest.approx(50.0)


def test_sharpe_ratio_is_zero_for_constant_returns():
    daily_returns = [1.0, 1.0, 1.0, 1.0]
    result = sharpe_ratio(daily_returns)
    assert result == 0.0


def test_annualized_volatility_is_positive_for_varying_returns():
    daily_returns = [1.0, -1.0, 2.0, -2.0, 0.5]
    result = annualized_volatility(daily_returns)
    assert result > 0