from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from backtest_predictor import numeric_value, run_walk_forward_backtest
from generate_report import StockDataFetcher
from src.research.backtest_engine import (
    SimulatedTrade,
    TradeCostConfig,
    simulate_trade,
)
from src.research.metrics import (
    annualized_volatility,
    cagr,
    max_drawdown,
    sharpe_ratio,
    win_rate,
)

OUTPUT_DIR = Path("output/backtests")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_trade_and_benchmark_returns(
    results_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
) -> tuple[list[float], list[float]]:
    """
    Convert backtest rows into non-overlapping trades and
    matched IHSG benchmark returns over the same holding windows.
    """
    cost_config = TradeCostConfig(cost_bps_per_side=20.0)
    trade_returns: list[float] = []
    benchmark_returns: list[float] = []

    holding_period_days = 5
    next_available_index = 0

    # Ensure benchmark has the expected columns.
    if not {"Date", "IHSG Close"}.issubset(benchmark_df.columns):
        return [], []

    benchmark_df = benchmark_df.sort_values("Date").reset_index(drop=True)

    for idx, row in results_df.reset_index(drop=True).iterrows():
        # Enforce non-overlapping positions: skip days inside an open trade.
        if idx < next_available_index:
            continue

        signal_score = int(row["Signal Score"])
        entry_price = numeric_value(row["Next-Day Open"])
        exit_price = numeric_value(row["Fifth-Day Close"])

        trade: SimulatedTrade | None = simulate_trade(
            signal_score=signal_score,
            entry_price=entry_price,
            exit_price=exit_price,
            cost_config=cost_config,
        )

        if trade is None:
            continue

        # Strategy trade return.
        trade_returns.append(trade.net_return_pct)
        next_available_index = idx + holding_period_days

        # Matched benchmark return for the same window.
        entry_date = pd.to_datetime(row["As Of Date"])
        exit_date = pd.to_datetime(row["Projected 5D End Date"])

        entry_idx = benchmark_df[
            benchmark_df["Date"] <= entry_date
        ].index.max()

        exit_idx = benchmark_df[
            benchmark_df["Date"] <= exit_date
        ].index.max()

        if (
            pd.isna(entry_idx)
            or pd.isna(exit_idx)
            or entry_idx == exit_idx
        ):
            benchmark_returns.append(0.0)
            continue

        entry_close = numeric_value(
            benchmark_df.iloc[entry_idx]["IHSG Close"]
        )
        exit_close = numeric_value(
            benchmark_df.iloc[exit_idx]["IHSG Close"]
        )

        if entry_close <= 0 or exit_close <= 0:
            benchmark_returns.append(0.0)
            continue

        benchmark_return_pct = (
            (exit_close / entry_close) - 1
        ) * 100

        benchmark_returns.append(benchmark_return_pct)

    return trade_returns, benchmark_returns


def build_equity_curve(returns_pct: list[float]) -> list[float]:
    """Compound returns into an equity index starting at 100."""
    equity = [100.0]

    for r in returns_pct:
        equity.append(equity[-1] * (1 + r / 100))

    return equity


def main() -> None:
    ticker = input("Ticker to backtest (e.g. BBCA): ").strip().upper()
    test_days = int(input("Number of test days (e.g. 250): ").strip())

    # Predictor walk-forward backtest (strategy signals).
    results_df, _, _ = run_walk_forward_backtest(ticker, test_days)

    # Fetch and validate IHSG benchmark data via existing engine.
    fetcher = StockDataFetcher()
    yahoo_data = fetcher.fetch_yahoo_data(ticker, period="2y")
    benchmark_df = yahoo_data.benchmark_price.copy()

    trade_returns, benchmark_returns = build_trade_and_benchmark_returns(
        results_df,
        benchmark_df,
    )

    if not trade_returns:
        print("No trades were generated (all signals were NEUTRAL).")
        return

    equity_curve_strategy = build_equity_curve(trade_returns)
    equity_curve_benchmark = build_equity_curve(benchmark_returns)
    total_days = len(results_df)

    metrics = {
        "ticker": ticker,
        "num_trades": len(trade_returns),
        "strategy": {
            "cumulative_return_pct": round(
                equity_curve_strategy[-1] - 100,
                2,
            ),
            "cagr_pct": round(
                cagr(
                    equity_curve_strategy[-1] - 100,
                    total_days,
                ),
                2,
            ),
            "annualized_volatility_pct": round(
                annualized_volatility(trade_returns),
                2,
            ),
            "sharpe_ratio": round(
                sharpe_ratio(trade_returns),
                2,
            ),
            "max_drawdown_pct": round(
                max_drawdown(equity_curve_strategy),
                2,
            ),
            "win_rate_pct": round(
                win_rate(trade_returns),
                2,
            ),
        },
        "benchmark_IHSG": {
            "cumulative_return_pct": round(
                equity_curve_benchmark[-1] - 100,
                2,
            ),
            "cagr_pct": round(
                cagr(
                    equity_curve_benchmark[-1] - 100,
                    total_days,
                ),
                2,
            ),
            "max_drawdown_pct": round(
                max_drawdown(equity_curve_benchmark),
                2,
            ),
        },
    }

    # Save equity curves as CSV.
    pd.DataFrame(
        {
            "strategy_equity": equity_curve_strategy,
            "benchmark_equity": equity_curve_benchmark,
        }
    ).to_csv(
        OUTPUT_DIR / f"{ticker}_equity_curve.csv",
        index=False,
    )

    # Save metrics as JSON artifact.
    with open(
        OUTPUT_DIR / f"{ticker}_metrics.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(metrics, f, indent=2)

    # Plot and save the overlay equity curve PNG.
    plt.figure(figsize=(10, 5))
    plt.plot(equity_curve_strategy, label=f"{ticker} strategy")
    plt.plot(
        equity_curve_benchmark,
        label="IHSG benchmark (same windows)",
    )
    plt.title(f"{ticker} Strategy vs IHSG Benchmark")
    plt.xlabel("Trade Number")
    plt.ylabel("Equity (Base 100)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / f"{ticker}_equity_curve.png",
    )

    # Also print metrics to the console.
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()