from __future__ import annotations

import numpy as np


def cagr(cumulative_return_pct: float, num_days: int) -> float:
    if num_days <= 0:
        raise ValueError("num_days must be positive")

    years = num_days / 365.25
    growth_factor = 1 + (cumulative_return_pct / 100)

    if growth_factor <= 0:
        return -100.0

    return (growth_factor ** (1 / years) - 1) * 100


def annualized_volatility(daily_returns_pct: list[float]) -> float:
    if len(daily_returns_pct) < 2:
        return 0.0

    daily_std = np.std(daily_returns_pct, ddof=1)
    return daily_std * np.sqrt(252)


def sharpe_ratio(
    daily_returns_pct: list[float],
    risk_free_rate_annual_pct: float = 0.0,
) -> float:
    if len(daily_returns_pct) < 2:
        return 0.0

    daily_rf = risk_free_rate_annual_pct / 252
    excess_returns = np.array(daily_returns_pct) - daily_rf
    mean_excess = np.mean(excess_returns)
    std_excess = np.std(excess_returns, ddof=1)

    if std_excess == 0:
        return 0.0

    return (mean_excess / std_excess) * np.sqrt(252)


def max_drawdown(equity_curve: list[float]) -> float:
    if len(equity_curve) < 2:
        return 0.0

    equity_array = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_array)
    drawdowns = (equity_array - running_max) / running_max
    return float(np.min(drawdowns)) * 100


def win_rate(trade_returns_pct: list[float]) -> float:
    if not trade_returns_pct:
        return 0.0

    wins = sum(1 for r in trade_returns_pct if r > 0)
    return (wins / len(trade_returns_pct)) * 100