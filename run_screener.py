from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from openpyxl.styles import Font, PatternFill
from src.analytics.decision import (
    DecisionInputs,
    RiskCategory,
    evaluate_trade_decision,
)

# ------------------------------------------------------------
# Reuse the already-loaded production classes when the
# screener is launched from generate_report.py.
#
# Fall back to importing generate_report when this file is
# executed directly with:
#
# python run_screener.py
# ------------------------------------------------------------

try:
    from __main__ import (
        DATA_DIR,
        OUTPUT_DIR,
        AnalyticsEngine,
        StockDataFetcher,
        logger,
    )
    from __main__ import (
        main as run_single_stock_report,
    )

except ImportError:
    from generate_report import (
        DATA_DIR,
        OUTPUT_DIR,
        AnalyticsEngine,
        StockDataFetcher,
        logger,
    )
    from generate_report import (
        main as run_single_stock_report,
    )


WATCHLIST_DIR = DATA_DIR / "watchlists"
SCREENER_OUTPUT_DIR = OUTPUT_DIR / "screeners"

DEFAULT_WATCHLIST_FILE = (
    WATCHLIST_DIR
    / "idx_watchlist.csv"
)

WATCHLIST_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

SCREENER_OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def safe_text(
    value: Any,
    fallback: str = "N/A",
) -> str:
    if value is None:
        return fallback

    text = str(value).strip()

    if not text or text.lower() == "nan":
        return fallback

    return text


def safe_number(
    value: Any,
    decimals: int = 2,
) -> str:
    try:
        number = float(value)

        if np.isnan(number) or np.isinf(number):
            return "N/A"

        return f"{number:,.{decimals}f}"

    except (TypeError, ValueError):
        return "N/A"


def numeric_value(
    value: Any,
    fallback: float = np.nan,
) -> float:
    try:
        number = float(value)

        if np.isnan(number) or np.isinf(number):
            return fallback

        return number

    except (TypeError, ValueError):
        return fallback

def load_backtest_status(
    ticker: str,
) -> tuple[str, str]:
    """Return cached backtest status without running a new backtest."""
    ticker_code = ticker.replace(".JK", "").upper()
    metrics_path = (
        OUTPUT_DIR
        / "backtests"
        / f"{ticker_code}_metrics.json"
    )

    if not metrics_path.exists():
        return (
            "NOT AVAILABLE",
            "Run the trade backtest before relying on historical validation.",
        )

    try:
        with metrics_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            backtest_metrics = json.load(file)

    except (OSError, json.JSONDecodeError):
        return (
            "INVALID",
            "Saved backtest metrics could not be read.",
        )

    strategy = backtest_metrics.get("strategy")
    benchmark = backtest_metrics.get("benchmark_IHSG")
    num_trades = backtest_metrics.get("num_trades")

    if (
        not isinstance(strategy, dict)
        or not isinstance(benchmark, dict)
        or not isinstance(num_trades, int)
    ):
        return (
            "INVALID",
            "Saved backtest metrics have an invalid structure.",
        )

    strategy_return = numeric_value(
        strategy.get("cumulative_return_pct")
    )
    benchmark_return = numeric_value(
        benchmark.get("cumulative_return_pct")
    )

    if pd.isna(strategy_return) or pd.isna(benchmark_return):
        return (
            "INVALID",
            "Saved backtest returns are missing or invalid.",
        )

    status_parts: list[str] = []

    if num_trades < 20:
        status_parts.append("SMALL SAMPLE")

    if strategy_return < benchmark_return:
        status_parts.append("UNDERPERFORMED IHSG")
    else:
        status_parts.append("OUTPERFORMED IHSG")

    return (
        " | ".join(status_parts),
        (
            f"Strategy {strategy_return:.2f}% vs IHSG "
            f"{benchmark_return:.2f}% across {num_trades} trades."
        ),
    )


def read_watchlist(
    watchlist_path: Path,
) -> list[str]:
    if not watchlist_path.exists():
        raise FileNotFoundError(
            "Watchlist file not found:\n"
            f"{watchlist_path}\n\n"
            "Create a CSV file with one required column:\n"
            "Ticker\n\n"
            "Example:\n"
            "Ticker\n"
            "MDIA\n"
            "ANTM\n"
            "BRIS\n"
        )

    watchlist_df = pd.read_csv(
        watchlist_path,
        dtype=str,
    )

    normalized_columns = {
        column.strip().lower(): column
        for column in watchlist_df.columns
    }

    if "ticker" not in normalized_columns:
        raise ValueError(
            "Watchlist CSV must contain a column named "
            "'Ticker'."
        )

    ticker_column = normalized_columns["ticker"]

    tickers = [
        ticker.strip().upper()
        for ticker in watchlist_df[ticker_column].dropna()
        if ticker.strip()
    ]

    tickers = list(dict.fromkeys(tickers))

    if not tickers:
        raise ValueError(
            "No ticker codes were found in the watchlist."
        )

    return tickers


def six_month_reporting_window(
    analyzed_df: pd.DataFrame,
) -> pd.DataFrame:
    if analyzed_df.empty:
        return analyzed_df.copy()

    latest_date = pd.to_datetime(
        analyzed_df["Date"].max()
    )

    cutoff_date = latest_date - pd.DateOffset(
        months=6,
    )

    return analyzed_df[
        analyzed_df["Date"] >= cutoff_date
    ].copy()


def build_screening_status(
    metrics: dict[str, Any],
    decision: str,
) -> tuple[str, int]:
    """Describe technical setup while enforcing the final decision gates."""
    normalized_decision = safe_text(decision).upper()

    minervini_passed = bool(
        metrics.get("minervini_passed")
    )
    extension_status = safe_text(
        metrics.get("extension_risk_status")
    )
    pullback_rrr = numeric_value(
        metrics.get("pullback_rrr")
    )
    breakout_rrr = numeric_value(
        metrics.get("breakout_rrr")
    )

    valid_pullback = (
        pd.notna(pullback_rrr)
        and pullback_rrr >= 2.0
    )
    valid_breakout = (
        pd.notna(breakout_rrr)
        and breakout_rrr >= 2.0
    )

    if normalized_decision == "INSUFFICIENT DATA":
        return (
            "INSUFFICIENT DATA - DO NOT RANK",
            1,
        )

    if normalized_decision == "AVOID":
        return (
            "AVOID - FINAL DECISION GATE",
            1,
        )

    if normalized_decision == "WAIT / NEUTRAL":
        if not minervini_passed:
            return (
                "WAIT - TREND TEMPLATE FAILED",
                2,
            )

        return (
            "WAIT - CONFIRMATION INCOMPLETE",
            2,
        )

    if normalized_decision == "WATCHLIST":
        if "BUYING CLIMAX" in extension_status.upper():
            return (
                "WATCHLIST - BUYING CLIMAX RISK",
                3,
            )

        if "EXTENDED" in extension_status.upper():
            return (
                "WATCHLIST - EXTENDED; WAIT FOR RESET",
                3,
            )

        if valid_pullback:
            return (
                "WATCHLIST - PULLBACK SETUP",
                3,
            )

        if valid_breakout:
            return (
                "WATCHLIST - BREAKOUT SETUP",
                3,
            )

        return (
            "WATCHLIST - WAIT FOR BETTER RISK/REWARD",
            3,
        )

    if normalized_decision == "CONSIDER ENTRY":
        if valid_pullback:
            return (
                "CONSIDER ENTRY - PULLBACK SETUP",
                5,
            )

        if valid_breakout:
            return (
                "CONSIDER ENTRY - BREAKOUT SETUP",
                5,
            )

        return (
            "CONSIDER ENTRY - REVIEW EXECUTION PLAN",
            5,
        )

    return (
        "WAIT - UNRECOGNIZED DECISION",
        1,
    )


def classify_finalist_queue(
    decision: str,
    screening_status: str,
) -> str:
    """Assign a watchlist queue using the final decision as the first gate."""
    normalized_decision = safe_text(decision).upper()
    normalized_status = safe_text(screening_status).upper()

    if normalized_decision == "CONSIDER ENTRY":
        if "PULLBACK" in normalized_status:
            return "01. Consider Entry - Pullback"

        if "BREAKOUT" in normalized_status:
            return "02. Consider Entry - Breakout"

        return "03. Consider Entry - Review"

    if normalized_decision == "WATCHLIST":
        return "04. Watchlist"

    if normalized_decision == "WAIT / NEUTRAL":
        return "05. Wait for Confirmation"

    if normalized_decision == "AVOID":
        return "06. Avoid"

    if normalized_decision == "INSUFFICIENT DATA":
        return "07. Insufficient Data"

    return "08. Unclassified"

def analyze_ticker(
    ticker: str,
    fetcher: StockDataFetcher,
    analytics: AnalyticsEngine,
) -> dict[str, Any]:
    yahoo_data = fetcher.fetch_yahoo_data(
        ticker,
        period="2y",
    )

    local_idx_data = pd.DataFrame()

    analyzed_df = analytics.calculate_indicators(
        yahoo_data.daily_price,
        yahoo_data.benchmark_price,
        local_idx_data,
    )

    report_df = six_month_reporting_window(
        analyzed_df
    )

    fundamentals = analytics.extract_fundamentals(
        yahoo_data.info,
        yahoo_data.balance_sheet,
        yahoo_data.income_statement,
        yahoo_data.cash_flow,
    )

    metrics = analytics.calculate_metrics(
        analyzed_df,
        fundamentals,
        report_df,
    )

    relative_strength_signal = safe_text(
        metrics.get("relative_strength_signal")
    )

    decision_inputs = DecisionInputs(
        has_sufficient_data=(
            numeric_value(
                metrics.get("data_coverage_percent")
            )
            >= 60
        ),
        trend_template_passed=bool(
            metrics.get("minervini_passed")
        ),
        relative_strength_positive=(
            "OUTPERFORMING" in relative_strength_signal.upper()
            or "BULLISH" in relative_strength_signal.upper()
            or "POSITIVE" in relative_strength_signal.upper()
        ),
        wyckoff_phase=safe_text(
            metrics.get("wyckoff_phase")
        ),
        extension_risk=(
            safe_text(
                metrics.get("extension_risk_status")
            )
            != "NORMAL"
        ),
        risk_reward_ratio=numeric_value(
            metrics.get("pullback_rrr")
        ),
        risk_category=(
            RiskCategory.SAFE
            if safe_text(metrics.get("risk_label"))
            == "SAFE (Bluechip / Liquid)"
            else (
                RiskCategory.MODERATE
                if safe_text(metrics.get("risk_label"))
                == "MODERATE RISK (Second Liner)"
                else (
                    RiskCategory.EXTREME
                    if safe_text(metrics.get("risk_label"))
                    == "EXTREME RISK (Saham Gorengan)"
                    else RiskCategory.UNKNOWN
                )
            )
        ),
    )

    trade_decision = evaluate_trade_decision(
        decision_inputs
    )

    risk_label = safe_text(metrics.get("risk_label"))

    if (
        risk_label == "MODERATE RISK (Second Liner)"
        and trade_decision.label.value == "CONSIDER ENTRY"
    ):
        trade_decision = trade_decision.__class__(
            label=trade_decision.label.WATCHLIST,
            confidence="Medium",
            reasons=(
                *trade_decision.reasons,
                "Moderate-risk second-liner: require extra liquidity review.",
            ),
            next_action=(
                "Keep on the watchlist. Review liquidity, spread, "
                "and position size before considering entry."
            ),
        )

    metrics["decision"] = trade_decision.label.value
    metrics["decision_confidence"] = trade_decision.confidence
    metrics["decision_next_action"] = trade_decision.next_action

    screening_status, priority = build_screening_status(
        metrics,
        trade_decision.label.value,
    )

    backtest_status, backtest_summary = load_backtest_status(
        yahoo_data.ticker
    )

    finalist_queue = classify_finalist_queue(
        trade_decision.label.value,
        screening_status,
    )

    minervini_checks = (
        f"{safe_text(metrics.get('minervini_passed_checks'))}"
        f"/{safe_text(metrics.get('minervini_total_checks'))}"
    )

    return {
        "Ticker": yahoo_data.ticker,
        "Company": safe_text(
            fundamentals.get("name")
        ),
        "Latest Date": pd.to_datetime(
            metrics.get("latest_date")
        ).strftime("%Y-%m-%d"),
        "Latest Close": numeric_value(
            metrics.get("latest_close")
        ),
        "Decision": trade_decision.label.value,
        "Decision Confidence": trade_decision.confidence,
        "Suggested Next Action": trade_decision.next_action,
        "Model Decision (Yahoo-only)": safe_text(
            metrics.get("decision")
        ),
        "Normalized Score": numeric_value(
            metrics.get("normalized_score")
        ),
        "Raw Score": safe_text(
            metrics.get("raw_score")
        ),
        "Data Coverage (%)": numeric_value(
            metrics.get("data_coverage_percent")
        ),
        "Relative Strength vs IHSG": relative_strength_signal,
        "Wyckoff Phase": safe_text(
            metrics.get("wyckoff_phase")
        ),
        "Minervini Status": (
            "PASSED"
            if metrics.get("minervini_passed")
            else "FAILED"
        ),
        "Minervini Checks": minervini_checks,
        "Extension Risk": safe_text(
            metrics.get("extension_risk_status")
        ),
        "Risk Classification": safe_text(
            metrics.get("risk_label")
        ),
        "Pullback RRR": numeric_value(
            metrics.get("pullback_rrr")
        ),
        "Breakout RRR": numeric_value(
            metrics.get("breakout_rrr")
        ),
        "Pullback Entry Low": numeric_value(
            metrics.get("pullback_entry_low")
        ),
        "Pullback Entry High": numeric_value(
            metrics.get("pullback_entry_high")
        ),
        "Breakout Trigger": numeric_value(
            metrics.get("breakout_entry")
        ),
        "Backtest Validation": backtest_status,
        "Backtest Summary": backtest_summary,
        "Finalist Queue": finalist_queue,
        "Screening Status": screening_status,
        "Screening Priority": priority,
        "Broker Data": "Not requested in screener",
        "Foreign Flow Data": "Not requested in screener",
    }


def create_excel_output(
    ranked_df: pd.DataFrame,
    errors_df: pd.DataFrame,
    output_path: Path,
    watchlist_path: Path,
    total_tickers: int,
) -> None:
    run_info_df = pd.DataFrame(
        [
            {
                "Run Time": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "Watchlist File": str(watchlist_path),
                "Total Tickers": total_tickers,
                "Successful Analyses": len(ranked_df),
                "Failed Analyses": len(errors_df),
                "Data Source": (
                    "Yahoo Finance only — "
                    "no Index Alpha API calls"
                ),
                "Ranking Rule": (
                    "Screening priority, then normalized score, "
                    "then breakout RRR"
                ),
            }
        ]
    )

    with pd.ExcelWriter(
        output_path,
        engine="openpyxl",
    ) as writer:
        ranked_df.to_excel(
            writer,
            sheet_name="Ranked Results",
            index=False,
        )

        queue_sheet_mapping = {
            "01. Consider Entry - Pullback": (
                "01 Entry Pullback"
            ),
            "02. Consider Entry - Breakout": (
                "02 Entry Breakout"
            ),
            "03. Consider Entry - Review": (
                "03 Entry Review"
            ),
            "04. Watchlist": "04 Watchlist",
            "05. Wait for Confirmation": (
                "05 Wait Confirmation"
            ),
            "06. Avoid": "06 Avoid",
            "07. Insufficient Data": "07 Insufficient Data",
            "08. Unclassified": "08 Unclassified",
        }

        for queue_name, sheet_name in (
            queue_sheet_mapping.items()
        ):
            queue_df = ranked_df[
                ranked_df["Finalist Queue"] == queue_name
            ].copy()

            queue_df.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False,
            )

        errors_df.to_excel(
            writer,
            sheet_name="Errors",
            index=False,
        )

        run_info_df.to_excel(
            writer,
            sheet_name="Run Info",
            index=False,
        )

        for worksheet in writer.book.worksheets:
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = (
                worksheet.dimensions
            )

            for column_cells in worksheet.columns:
                column_letter = (
                    column_cells[0].column_letter
                )

                maximum_length = max(
                    len(
                        str(cell.value)
                        if cell.value is not None
                        else ""
                    )
                    for cell in column_cells
                )

                worksheet.column_dimensions[
                    column_letter
                ].width = min(
                    max(maximum_length + 2, 12),
                    38,
                )

            for cell in worksheet[1]:
                cell.font = Font(
                    bold=True,
                    color="FFFFFF",
                )

                cell.fill = PatternFill(
                    fill_type="solid",
                    fgColor="1B365D",
                )

    logger.info(
        "Saved screener Excel output: %s",
        output_path,
    )


def print_ranked_results(
    ranked_df: pd.DataFrame,
) -> None:
    if ranked_df.empty:
        print()
        print(
            "No ticker analyses were completed successfully."
        )
        return

    display_columns = [
        "Rank",
        "Ticker",
        "Model Decision (Yahoo-only)",
        "Normalized Score",
        "Wyckoff Phase",
        "Minervini Status",
        "Extension Risk",
        "Pullback RRR",
        "Breakout RRR",
        "Screening Status",
    ]

    display_df = ranked_df[
        display_columns
    ].copy()

    display_df["Normalized Score"] = (
        display_df["Normalized Score"].map(
            lambda value: safe_number(value, 1)
        )
    )

    display_df["Pullback RRR"] = (
        display_df["Pullback RRR"].map(
            lambda value: safe_number(value, 2)
        )
    )

    display_df["Breakout RRR"] = (
        display_df["Breakout RRR"].map(
            lambda value: safe_number(value, 2)
        )
    )

    print()
    print("=" * 112)
    print("TOP SCREENING RESULTS")
    print("=" * 112)
    print(
        display_df.to_string(
            index=False,
        )
    )

def print_finalist_queue(
    ranked_df: pd.DataFrame,
) -> None:
    if ranked_df.empty:
        return

    display_columns = [
        "Rank",
        "Ticker",
        "Decision",
        "Decision Confidence",
        "Normalized Score",
        "Relative Strength vs IHSG",
        "Wyckoff Phase",
        "Minervini Status",
        "Extension Risk",
        "Pullback RRR",
        "Breakout RRR",
        "Risk Classification",
        "Backtest Validation",
        "Screening Status",
    ]

    queue_order = [
        "01. Consider Entry - Pullback",
        "02. Consider Entry - Breakout",
        "03. Consider Entry - Review",
        "04. Watchlist",
        "05. Wait for Confirmation",
        "06. Avoid",
        "07. Insufficient Data",
        "08. Unclassified",
    ]

    queue_titles = {
        "01. Consider Entry - Pullback": (
            "CONSIDER ENTRY - PULLBACK SETUPS"
        ),
        "02. Consider Entry - Breakout": (
            "CONSIDER ENTRY - BREAKOUT SETUPS"
        ),
        "03. Consider Entry - Review": (
            "CONSIDER ENTRY - REVIEW EXECUTION"
        ),
        "04. Watchlist": "WATCHLIST - WAIT FOR CONFIRMATION",
        "05. Wait for Confirmation": (
            "WAIT / NEUTRAL - CONFIRMATION INCOMPLETE"
        ),
        "06. Avoid": "AVOID - FINAL DECISION GATE",
        "07. Insufficient Data": (
            "INSUFFICIENT DATA - DO NOT ACT"
        ),
        "08. Unclassified": "UNCLASSIFIED RESULTS",
    }

    print()
    print("=" * 112)
    print("FINALIST QUEUE")
    print("=" * 112)

    for queue_name in queue_order:
        queue_df = ranked_df[
            ranked_df["Finalist Queue"] == queue_name
        ].copy()

        print()
        print(queue_titles[queue_name])
        print("-" * 112)

        if queue_df.empty:
            print("None")
            continue

        display_df = queue_df[
            display_columns
        ].copy()

        display_df["Normalized Score"] = (
            display_df["Normalized Score"].map(
                lambda value: safe_number(value, 1)
            )
        )

        display_df["Pullback RRR"] = (
            display_df["Pullback RRR"].map(
                lambda value: safe_number(value, 2)
            )
        )

        display_df["Breakout RRR"] = (
            display_df["Breakout RRR"].map(
                lambda value: safe_number(value, 2)
            )
        )

        print(
            display_df.to_string(
                index=False,
            )
        )

def offer_deep_dive_handoff(
    ranked_df: pd.DataFrame,
) -> None:
    if ranked_df.empty:
        return

    eligible_queues = [
        "01. Consider Entry - Pullback",
        "02. Consider Entry - Breakout",
        "03. Consider Entry - Review",
        "04. Watchlist",
    ]

    finalists_df = ranked_df[
        ranked_df["Finalist Queue"].isin(
            eligible_queues
        )
    ].copy()

    if finalists_df.empty:
        print()
        print(
            "No structurally valid finalists are "
            "available for deep-dive analysis."
        )
        return

    print()

    run_deep_dive = input(
        "Run detailed analysis for a finalist? [Y/N]: "
    ).strip().upper()

    if run_deep_dive != "Y":
        return

    finalists_df = finalists_df.reset_index(
        drop=True
    )

    print()
    print("=" * 68)
    print("DEEP-DIVE FINALIST SELECTION")
    print("=" * 68)

    for index, row in finalists_df.iterrows():
        print(
            f"{index + 1}. "
            f"{row['Ticker']} | "
            f"{row['Screening Status']} | "
            f"Score: "
            f"{safe_number(row['Normalized Score'], 1)}"
        )

    print()

    selection_input = input(
        "Select ticker number or press Enter to cancel: "
    ).strip()

    if not selection_input:
        print("Deep-dive handoff cancelled.")
        return

    try:
        selected_index = int(selection_input) - 1

        if (
            selected_index < 0
            or selected_index >= len(finalists_df)
        ):
            raise ValueError

    except ValueError:
        print("Invalid finalist selection.")
        return

    selected_ticker = finalists_df.iloc[
        selected_index
    ]["Ticker"]

    print()
    print("=" * 68)
    print(
        "STARTING FULL DEEP-DIVE ANALYSIS FOR "
        f"{selected_ticker}"
    )
    print("=" * 68)
    print()

    run_single_stock_report(
        preselected_ticker=selected_ticker,
        skip_workflow_menu=True,
    )

def main() -> None:
    print()
    print("=" * 68)
    print("IDX BATCH SWING SCREENER")
    print("=" * 68)
    print()
    print(
        "Mode: Yahoo-only pre-screening "
        "(no Index Alpha API calls)"
    )
    print(
        f"Default watchlist: {DEFAULT_WATCHLIST_FILE}"
    )
    print()

    watchlist_input = input(
        "Press Enter for default watchlist or enter CSV path: "
    ).strip()

    watchlist_path = (
        Path(watchlist_input)
        if watchlist_input
        else DEFAULT_WATCHLIST_FILE
    )

    try:
        tickers = read_watchlist(
            watchlist_path
        )

    except Exception as error:
        print()
        print("WATCHLIST ERROR")
        print("-" * 68)
        print(error)
        return

    print()
    print(
        f"Watchlist loaded: {len(tickers)} ticker(s)"
    )
    print()

    fetcher = StockDataFetcher()
    analytics = AnalyticsEngine()

    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for index, ticker in enumerate(
        tickers,
        start=1,
    ):
        print(
            f"[{index}/{len(tickers)}] "
            f"Screening {ticker}..."
        )

        try:
            result = analyze_ticker(
                ticker,
                fetcher,
                analytics,
            )

            results.append(result)

            print(
                f"  {result['Screening Status']} | "
                f"Score: "
                f"{safe_number(result['Normalized Score'], 1)}"
            )

        except Exception as error:
            logger.exception(
                "Screener failed for %s",
                ticker,
            )

            errors.append(
                {
                    "Ticker": ticker,
                    "Error": str(error),
                }
            )

            print(
                f"  FAILED: {error}"
            )

    ranked_df = pd.DataFrame(results)
    errors_df = pd.DataFrame(
        errors,
        columns=["Ticker", "Error"],
    )

    if not ranked_df.empty:
        ranked_df = ranked_df.sort_values(
            by=[
                "Screening Priority",
                "Normalized Score",
                "Breakout RRR",
            ],
            ascending=[
                False,
                False,
                False,
            ],
            na_position="last",
        ).reset_index(
            drop=True
        )

        ranked_df.insert(
            0,
            "Rank",
            range(1, len(ranked_df) + 1),
        )

    generated_at = datetime.now().strftime(
        "%Y%m%d_%H%M"
    )

    csv_output_path = (
        SCREENER_OUTPUT_DIR
        / f"IDX_Swing_Screener_{generated_at}.csv"
    )

    excel_output_path = (
        SCREENER_OUTPUT_DIR
        / f"IDX_Swing_Screener_{generated_at}.xlsx"
    )

    ranked_df.to_csv(
        csv_output_path,
        index=False,
    )

    create_excel_output(
        ranked_df,
        errors_df,
        excel_output_path,
        watchlist_path,
        len(tickers),
    )

    print_finalist_queue(
        ranked_df
    )

    print()
    print("=" * 68)
    print("SCREENER COMPLETED")
    print("=" * 68)
    print(
        f"Tickers requested: {len(tickers)}"
    )
    print(
        f"Successful analyses: {len(ranked_df)}"
    )
    print(
        f"Failed analyses: {len(errors_df)}"
    )
    print()
    print("Generated CSV screener:")
    print(csv_output_path)
    print()
    print("Generated Excel screener:")
    print(excel_output_path)
    offer_deep_dive_handoff(
        ranked_df
    )


if __name__ == "__main__":
    main()