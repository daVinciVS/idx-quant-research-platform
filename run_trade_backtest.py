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

HOLDING_PERIOD_DAYS = 5
COST_BPS_PER_SIDE = 20.0
INITIAL_EQUITY = 100.0


def benchmark_return_for_trade(
    benchmark_df: pd.DataFrame,
    entry_date: pd.Timestamp,
    exit_date: pd.Timestamp,
) -> float:
    """Return IHSG close-to-close percentage return for one trade window."""
    benchmark_at_entry = benchmark_df[
        benchmark_df["Date"] <= entry_date
    ]
    benchmark_at_exit = benchmark_df[
        benchmark_df["Date"] <= exit_date
    ]

    if benchmark_at_entry.empty or benchmark_at_exit.empty:
        return 0.0

    entry_close = numeric_value(
        benchmark_at_entry.iloc[-1]["IHSG Close"]
    )
    exit_close = numeric_value(
        benchmark_at_exit.iloc[-1]["IHSG Close"]
    )

    if entry_close <= 0 or exit_close <= 0:
        return 0.0

    return ((exit_close / entry_close) - 1) * 100


def build_trade_ledger(
    results_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build a non-overlapping, long-only ledger from walk-forward signals.

    Signals are formed at the signal-date close. A position is entered at
    the next-session open, held for five sessions, and exited at the fifth
    session close. Each side incurs the configured transaction cost.
    """
    required_result_columns = {
        "As Of Date",
        "Projected Next Session",
        "Projected 5D End Date",
        "Next-Day Open",
        "Fifth-Day Close",
        "Signal Score",
    }
    required_benchmark_columns = {"Date", "IHSG Close"}

    if not required_result_columns.issubset(results_df.columns):
        missing = sorted(
            required_result_columns.difference(results_df.columns)
        )
        raise ValueError(
            f"Backtest results are missing required columns: {missing}"
        )

    if not required_benchmark_columns.issubset(benchmark_df.columns):
        missing = sorted(
            required_benchmark_columns.difference(benchmark_df.columns)
        )
        raise ValueError(
            f"Benchmark data is missing required columns: {missing}"
        )

    cost_config = TradeCostConfig(
        cost_bps_per_side=COST_BPS_PER_SIDE
    )
    benchmark_df = benchmark_df.sort_values("Date").reset_index(drop=True)
    ledger_rows: list[dict[str, float | int | str]] = []
    next_available_index = 0
    strategy_equity = INITIAL_EQUITY
    benchmark_equity = INITIAL_EQUITY

    for index, row in results_df.reset_index(drop=True).iterrows():
        if index < next_available_index:
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

        signal_date = pd.to_datetime(row["As Of Date"])
        entry_date = pd.to_datetime(row["Projected Next Session"])
        exit_date = pd.to_datetime(row["Projected 5D End Date"])

        benchmark_return_pct = benchmark_return_for_trade(
            benchmark_df,
            entry_date,
            exit_date,
        )

        strategy_equity *= 1 + (trade.net_return_pct / 100)
        benchmark_equity *= 1 + (benchmark_return_pct / 100)

        ledger_rows.append(
            {
                "signal_date": signal_date.date().isoformat(),
                "entry_date": entry_date.date().isoformat(),
                "exit_date": exit_date.date().isoformat(),
                "signal_score": signal_score,
                "entry_price": round(trade.entry_price, 2),
                "exit_price": round(trade.exit_price, 2),
                "gross_return_pct": round(trade.gross_return_pct, 4),
                "round_trip_cost_pct": round(
                    COST_BPS_PER_SIDE * 2 / 100,
                    4,
                ),
                "net_return_pct": round(trade.net_return_pct, 4),
                "strategy_equity": round(strategy_equity, 4),
                "ihsg_return_pct": round(benchmark_return_pct, 4),
                "benchmark_equity": round(benchmark_equity, 4),
            }
        )

        next_available_index = index + HOLDING_PERIOD_DAYS

    return pd.DataFrame(ledger_rows)


def build_equity_curve(
    ledger_df: pd.DataFrame,
    column_name: str,
) -> list[float]:
    """Return an equity curve including its initial base value."""
    if ledger_df.empty:
        return [INITIAL_EQUITY]

    return [
        INITIAL_EQUITY,
        *ledger_df[column_name].astype(float).tolist(),
    ]


def build_metrics(
    ticker: str,
    results_df: pd.DataFrame,
    ledger_df: pd.DataFrame,
) -> dict[str, object]:
    """Build transparent strategy and matched-benchmark performance metrics."""
    strategy_returns = ledger_df["net_return_pct"].astype(float).tolist()
    benchmark_returns = ledger_df["ihsg_return_pct"].astype(float).tolist()

    strategy_equity = build_equity_curve(
        ledger_df,
        "strategy_equity",
    )
    benchmark_equity = build_equity_curve(
        ledger_df,
        "benchmark_equity",
    )

    total_days = len(results_df)

    return {
        "ticker": ticker,
        "test_observations": total_days,
        "num_trades": len(ledger_df),
        "holding_period_days": HOLDING_PERIOD_DAYS,
        "cost_bps_per_side": COST_BPS_PER_SIDE,
        "round_trip_cost_pct": round(
            COST_BPS_PER_SIDE * 2 / 100,
            2,
        ),
        "strategy": {
            "cumulative_return_pct": round(
                strategy_equity[-1] - INITIAL_EQUITY,
                2,
            ),
            "cagr_pct": round(
                cagr(
                    strategy_equity[-1] - INITIAL_EQUITY,
                    total_days,
                ),
                2,
            ),
            "annualized_volatility_pct": round(
                annualized_volatility(strategy_returns),
                2,
            ),
            "sharpe_ratio": round(
                sharpe_ratio(strategy_returns),
                2,
            ),
            "max_drawdown_pct": round(
                max_drawdown(strategy_equity),
                2,
            ),
            "win_rate_pct": round(
                win_rate(strategy_returns),
                2,
            ),
        },
        "benchmark_IHSG": {
            "cumulative_return_pct": round(
                benchmark_equity[-1] - INITIAL_EQUITY,
                2,
            ),
            "cagr_pct": round(
                cagr(
                    benchmark_equity[-1] - INITIAL_EQUITY,
                    total_days,
                ),
                2,
            ),
            "annualized_volatility_pct": round(
                annualized_volatility(benchmark_returns),
                2,
            ),
            "sharpe_ratio": round(
                sharpe_ratio(benchmark_returns),
                2,
            ),
            "max_drawdown_pct": round(
                max_drawdown(benchmark_equity),
                2,
            ),
        },
    }


def save_backtest_artifacts(
    ticker: str,
    ledger_df: pd.DataFrame,
    metrics: dict[str, object],
) -> None:
    """Save an auditable ledger, equity curves, metrics, and chart."""
    strategy_equity = build_equity_curve(
        ledger_df,
        "strategy_equity",
    )
    benchmark_equity = build_equity_curve(
        ledger_df,
        "benchmark_equity",
    )

    ledger_df.to_csv(
        OUTPUT_DIR / f"{ticker}_trade_ledger.csv",
        index=False,
    )

    ledger_excel_path = OUTPUT_DIR / f"{ticker}_trade_ledger.xlsx"

    with pd.ExcelWriter(
        ledger_excel_path,
        engine="openpyxl",
    ) as writer:
        ledger_df.to_excel(
            writer,
            sheet_name="Trade Ledger",
            index=False,
        )

        worksheet = writer.sheets["Trade Ledger"]
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions

        price_columns = {
            "entry_price",
            "exit_price",
            "strategy_equity",
            "benchmark_equity",
        }
        percent_columns = {
            "gross_return_pct",
            "round_trip_cost_pct",
            "net_return_pct",
            "ihsg_return_pct",
        }

        for column_cells in worksheet.columns:
            column_letter = column_cells[0].column_letter
            header = column_cells[0].value
            maximum_length = max(
                len(str(cell.value or ""))
                for cell in column_cells
            )

            worksheet.column_dimensions[
                column_letter
            ].width = min(maximum_length + 2, 28)

            if header in price_columns:
                for cell in column_cells[1:]:
                    cell.number_format = "#,##0.00"

            if header in percent_columns:
                for cell in column_cells[1:]:
                    cell.number_format = '0.00"%"'

    pd.DataFrame(
        {
            "trade_number": range(len(strategy_equity)),
            "strategy_equity": strategy_equity,
            "benchmark_equity": benchmark_equity,
        }
    ).to_csv(
        OUTPUT_DIR / f"{ticker}_equity_curve.csv",
        index=False,
    )

    with (OUTPUT_DIR / f"{ticker}_metrics.json").open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(metrics, file, indent=2)

    plt.figure(figsize=(10, 5))
    plt.plot(strategy_equity, label=f"{ticker} strategy")
    plt.plot(
        benchmark_equity,
        label="IHSG benchmark (matched trade windows)",
    )
    plt.title(f"{ticker} Strategy vs IHSG Benchmark")
    plt.xlabel("Trade Number")
    plt.ylabel("Equity (Base 100)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / f"{ticker}_equity_curve.png",
        dpi=150,
    )
    plt.close()


def main() -> None:
    ticker = input("Ticker to backtest (e.g. BBCA): ").strip().upper()
    test_days = int(
        input("Number of test days (e.g. 250): ").strip()
    )

    results_df, _, _ = run_walk_forward_backtest(
        ticker,
        test_days,
    )

    fetcher = StockDataFetcher()
    yahoo_data = fetcher.fetch_yahoo_data(
        ticker,
        period="2y",
    )
    benchmark_df = yahoo_data.benchmark_price.copy()

    ledger_df = build_trade_ledger(
        results_df,
        benchmark_df,
    )

    if ledger_df.empty:
        print("No qualifying long trades were generated.")
        return

    metrics = build_metrics(
        ticker,
        results_df,
        ledger_df,
    )

    save_backtest_artifacts(
        ticker,
        ledger_df,
        metrics,
    )

    print(json.dumps(metrics, indent=2))
    print()
    print("Saved backtest artifacts:")
    print(OUTPUT_DIR / f"{ticker}_trade_ledger.csv")
    print(OUTPUT_DIR / f"{ticker}_trade_ledger.xlsx")
    print(OUTPUT_DIR / f"{ticker}_equity_curve.csv")
    print(OUTPUT_DIR / f"{ticker}_metrics.json")
    print(OUTPUT_DIR / f"{ticker}_equity_curve.png")


if __name__ == "__main__":
    main()