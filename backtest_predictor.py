from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from openpyxl.styles import Font, PatternFill

from run_predictor import (
    calculate_projection_signals,
    calculate_scenarios,
)


try:
    from __main__ import (
        AnalyticsEngine,
        OUTPUT_DIR,
        StockDataFetcher,
        logger,
    )

except ImportError:
    from generate_report import (
        AnalyticsEngine,
        OUTPUT_DIR,
        StockDataFetcher,
        logger,
    )


BACKTEST_OUTPUT_DIR = OUTPUT_DIR / "backtests"

BACKTEST_OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


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


def score_bucket(
    signal_score: int,
) -> str:
    if signal_score >= 4:
        return "Score >= +4"

    if signal_score >= 1:
        return "Score +1 to +3"

    if signal_score == 0:
        return "Score 0"

    if signal_score >= -3:
        return "Score -1 to -3"

    return "Score <= -4"


def predicted_direction(
    signal_score: int,
) -> str:
    if signal_score >= 1:
        return "BULLISH"

    if signal_score <= -1:
        return "BEARISH"

    return "NEUTRAL"


def actual_direction(
    return_percent: float,
) -> str:
    if return_percent > 0.001:
        return "BULLISH"

    if return_percent < -0.001:
        return "BEARISH"

    return "NEUTRAL"


def direction_hit(
    predicted: str,
    actual: str,
) -> bool | float:
    # A neutral score makes no bullish or bearish forecast.
    # Return NaN so Pandas excludes it from directional
    # hit-rate calculations.
    if predicted == "NEUTRAL":
        return np.nan

    return predicted == actual


def six_month_window(
    analyzed_df: pd.DataFrame,
) -> pd.DataFrame:
    latest_date = pd.to_datetime(
        analyzed_df["Date"].max()
    )

    cutoff_date = latest_date - pd.DateOffset(
        months=6,
    )

    return analyzed_df[
        analyzed_df["Date"] >= cutoff_date
    ].copy()

def summarize_subset(
    rule_name: str,
    subset_df: pd.DataFrame,
) -> dict[str, Any]:
    evaluated_df = subset_df.dropna(
        subset=[
            "Next Direction Hit",
            "5D Direction Hit",
        ]
    ).copy()

    start_date = (
        pd.to_datetime(
            subset_df["As Of Date"]
        ).min()
        if not subset_df.empty
        else pd.NaT
    )

    end_date = (
        pd.to_datetime(
            subset_df["As Of Date"]
        ).max()
        if not subset_df.empty
        else pd.NaT
    )

    return {
        "Rule Set": rule_name,
        "Signals": len(subset_df),
        "Directional Observations": len(evaluated_df),
        "Period Start": start_date,
        "Period End": end_date,
        "Next-Day Direction Hit Rate (%)": (
            evaluated_df["Next Direction Hit"].mean()
            * 100
            if not evaluated_df.empty
            else np.nan
        ),
        "5-Day Direction Hit Rate (%)": (
            evaluated_df["5D Direction Hit"].mean()
            * 100
            if not evaluated_df.empty
            else np.nan
        ),
        "Average Next-Day Return (%)": (
            subset_df["Next-Day Return (%)"].mean()
            if not subset_df.empty
            else np.nan
        ),
        "Average 5-Day Return (%)": (
            subset_df["5-Day Return (%)"].mean()
            if not subset_df.empty
            else np.nan
        ),
        "Average 5D Favorable Move (%)": (
            subset_df["5D Favorable Move (%)"].mean()
            if not subset_df.empty
            else np.nan
        ),
        "Average 5D Adverse Move (%)": (
            subset_df["5D Adverse Move (%)"].mean()
            if not subset_df.empty
            else np.nan
        ),
    }


def build_quality_filter_summary(
    results_df: pd.DataFrame,
) -> pd.DataFrame:
    bullish_score = (
        results_df["Signal Score"] >= 4
    )

    minervini_passed = (
        results_df["Minervini Passed"] == True
    )

    normal_extension = (
        results_df["Extension Risk"]
        .fillna("")
        .astype(str)
        .str.upper()
        .eq("NORMAL")
    )

    markup_phase = (
        results_df["Wyckoff Phase"]
        .fillna("")
        .astype(str)
        .str.upper()
        .eq("MARKUP PHASE")
    )

    rule_sets = [
        (
            "Score >= +4",
            bullish_score,
        ),
        (
            "Score >= +4 + Minervini Passed",
            bullish_score
            & minervini_passed,
        ),
        (
            "Score >= +4 + Minervini Passed "
            "+ Normal Extension",
            bullish_score
            & minervini_passed
            & normal_extension,
        ),
        (
            "Score >= +4 + Minervini Passed "
            "+ Normal Extension + Markup",
            bullish_score
            & minervini_passed
            & normal_extension
            & markup_phase,
        ),
    ]

    summary_rows = []

    for rule_name, mask in rule_sets:
        subset_df = results_df[
            mask
        ].copy()

        summary_rows.append(
            summarize_subset(
                rule_name,
                subset_df,
            )
        )

    return pd.DataFrame(summary_rows)


def build_chronological_summary(
    results_df: pd.DataFrame,
) -> pd.DataFrame:
    bullish_df = results_df[
        results_df["Signal Score"] >= 4
    ].copy()

    if bullish_df.empty:
        return pd.DataFrame()

    bullish_df["As Of Date"] = pd.to_datetime(
        bullish_df["As Of Date"]
    )

    bullish_df = bullish_df.sort_values(
        "As Of Date"
    ).reset_index(
        drop=True
    )

    split_index = len(bullish_df) // 2

    older_df = bullish_df.iloc[
        :split_index
    ].copy()

    recent_df = bullish_df.iloc[
        split_index:
    ].copy()

    return pd.DataFrame(
        [
            summarize_subset(
                "Score >= +4 — Older Half",
                older_df,
            ),
            summarize_subset(
                "Score >= +4 — Recent Half",
                recent_df,
            ),
        ]
    )

def build_summary(
    results_df: pd.DataFrame,
) -> pd.DataFrame:
    if results_df.empty:
        return pd.DataFrame()

    summary_rows = []

    for bucket, bucket_df in results_df.groupby(
        "Score Bucket",
        sort=False,
    ):
        next_hit_rate = (
            bucket_df["Next Direction Hit"]
            .mean()
            * 100
        )

        five_day_hit_rate = (
            bucket_df["5D Direction Hit"]
            .mean()
            * 100
        )

        next_range_coverage = (
            bucket_df["Next Range Covered"]
            .mean()
            * 100
        )

        bullish_target_hit_rate = (
            bucket_df["Bullish Scenario Hit"]
            .mean()
            * 100
        )

        bearish_target_hit_rate = (
            bucket_df["Bearish Scenario Hit"]
            .mean()
            * 100
        )

        summary_rows.append(
            {
                "Score Bucket": bucket,
                "Signals": len(bucket_df),
                "Next-Day Direction Hit Rate (%)": (
                    next_hit_rate
                ),
                "5-Day Direction Hit Rate (%)": (
                    five_day_hit_rate
                ),
                "Next-Day ATR Range Coverage (%)": (
                    next_range_coverage
                ),
                "Bullish 5D Scenario Hit Rate (%)": (
                    bullish_target_hit_rate
                ),
                "Bearish 5D Scenario Hit Rate (%)": (
                    bearish_target_hit_rate
                ),
                "Average Next-Day Return (%)": (
                    bucket_df["Next-Day Return (%)"].mean()
                ),
                "Average 5-Day Return (%)": (
                    bucket_df["5-Day Return (%)"].mean()
                ),
                "Average 5D Favorable Move (%)": (
                    bucket_df["5D Favorable Move (%)"].mean()
                ),
                "Average 5D Adverse Move (%)": (
                    bucket_df["5D Adverse Move (%)"].mean()
                ),
            }
        )

    summary_df = pd.DataFrame(summary_rows)

    bucket_order = [
        "Score >= +4",
        "Score +1 to +3",
        "Score 0",
        "Score -1 to -3",
        "Score <= -4",
    ]

    summary_df["Sort Order"] = summary_df[
        "Score Bucket"
    ].map(
        {
            bucket: index
            for index, bucket in enumerate(
                bucket_order
            )
        }
    )

    summary_df = summary_df.sort_values(
        "Sort Order"
    ).drop(
        columns="Sort Order"
    )

    return summary_df.reset_index(
        drop=True
    )


def write_excel_output(
    results_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    quality_filter_df: pd.DataFrame,
    chronological_df: pd.DataFrame,
    run_info_df: pd.DataFrame,
    output_path: Path,
) -> None:
    with pd.ExcelWriter(
        output_path,
        engine="openpyxl",
    ) as writer:
        results_df.to_excel(
            writer,
            sheet_name="Walk Forward Results",
            index=False,
        )

        summary_df.to_excel(
            writer,
            sheet_name="Score Summary",
            index=False,
        )

        quality_filter_df.to_excel(
            writer,
            sheet_name="Quality Filters",
            index=False,
        )

        chronological_df.to_excel(
            writer,
            sheet_name="Time Split",
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

            for cell in worksheet[1]:
                cell.font = Font(
                    bold=True,
                    color="FFFFFF",
                )

                cell.fill = PatternFill(
                    fill_type="solid",
                    fgColor="1B365D",
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
                    42,
                )


def run_walk_forward_backtest(
    ticker_input: str,
    test_days: int,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    fetcher = StockDataFetcher()
    analytics = AnalyticsEngine()

    yahoo_data = fetcher.fetch_yahoo_data(
        ticker_input,
        period="2y",
    )

    fundamentals = analytics.extract_fundamentals(
        yahoo_data.info,
        yahoo_data.balance_sheet,
        yahoo_data.income_statement,
        yahoo_data.cash_flow,
    )

    full_daily_df = yahoo_data.daily_price.copy()

    minimum_history_days = 220
    future_horizon_days = 5

    maximum_test_index = (
        len(full_daily_df)
        - future_horizon_days
        - 1
    )

    minimum_test_index = minimum_history_days

    available_test_days = (
        maximum_test_index
        - minimum_test_index
        + 1
    )

    if available_test_days <= 0:
        raise RuntimeError(
            "Insufficient completed price history for "
            "a 200-day-indicator walk-forward backtest."
        )

    effective_test_days = min(
        test_days,
        available_test_days,
    )

    start_index = (
        maximum_test_index
        - effective_test_days
        + 1
    )

    print()
    print(
        "Walk-forward test window: "
        f"{full_daily_df.iloc[start_index]['Date'].strftime('%Y-%m-%d')} "
        "to "
        f"{full_daily_df.iloc[maximum_test_index]['Date'].strftime('%Y-%m-%d')}"
    )

    results: list[dict[str, Any]] = []

    for test_index in range(
        start_index,
        maximum_test_index + 1,
    ):
        historical_daily_df = full_daily_df.iloc[
            : test_index + 1
        ].copy()

        as_of_date = historical_daily_df.iloc[
            -1
        ]["Date"]

        historical_benchmark_df = (
            yahoo_data.benchmark_price[
                yahoo_data.benchmark_price["Date"]
                <= as_of_date
            ]
            .copy()
        )

        analyzed_df = analytics.calculate_indicators(
            historical_daily_df,
            historical_benchmark_df,
            pd.DataFrame(),
        )

        report_df = six_month_window(
            analyzed_df
        )

        metrics = analytics.calculate_metrics(
            analyzed_df,
            fundamentals,
            report_df,
        )

        signal_score, _ = (
            calculate_projection_signals(
                metrics
            )
        )

        close_price = numeric_value(
            metrics.get("latest_close")
        )

        atr14 = numeric_value(
            metrics.get("atr14")
        )

        if (
            pd.isna(close_price)
            or pd.isna(atr14)
            or atr14 <= 0
        ):
            continue

        projection = calculate_scenarios(
            close_price,
            atr14,
            signal_score,
        )

        next_day = full_daily_df.iloc[
            test_index + 1
        ]

        five_day_window = full_daily_df.iloc[
            test_index + 1:
            test_index + 1 + future_horizon_days
        ].copy()

        next_day_close = numeric_value(
            next_day["Close"]
        )

        next_day_high = numeric_value(
            next_day["High"]
        )

        next_day_low = numeric_value(
            next_day["Low"]
        )

        fifth_day_close = numeric_value(
            five_day_window.iloc[-1]["Close"]
        )

        next_day_return = (
            (next_day_close / close_price) - 1
        ) * 100

        five_day_return = (
            (fifth_day_close / close_price) - 1
        ) * 100

        predicted_next_direction = predicted_direction(
            signal_score
        )

        actual_next_direction = actual_direction(
            next_day_return / 100
        )

        actual_five_day_direction = actual_direction(
            five_day_return / 100
        )

        next_range_covered = (
            next_day_low >= projection["next_day_low"]
            and next_day_high <= projection["next_day_high"]
        )

        bullish_scenario_hit = (
            five_day_window["High"].max()
            >= projection["bullish_high"]
        )

        bearish_scenario_hit = (
            five_day_window["Low"].min()
            <= projection["bearish_low"]
        )

        max_high = numeric_value(
            five_day_window["High"].max()
        )

        min_low = numeric_value(
            five_day_window["Low"].min()
        )

        if signal_score >= 1:
            favorable_move = (
                (max_high / close_price) - 1
            ) * 100

            adverse_move = (
                (min_low / close_price) - 1
            ) * 100

        elif signal_score <= -1:
            favorable_move = (
                (close_price / min_low) - 1
            ) * 100

            adverse_move = (
                (close_price / max_high) - 1
            ) * 100

        else:
            favorable_move = np.nan
            adverse_move = np.nan

        results.append(
            {
                "As Of Date": as_of_date,
                "Projected Next Session": next_day[
                    "Date"
                ],
                "Projected 5D End Date": five_day_window.iloc[
                    -1
                ]["Date"],
                "Close At Signal": close_price,
                "ATR14": atr14,
                "Signal Score": signal_score,
                "Score Bucket": score_bucket(
                    signal_score
                ),
                "Minervini Passed": bool(
                    metrics.get("minervini_passed")
                ),
                "Extension Risk": metrics.get(
                    "extension_risk_status"
                ),
                "Wyckoff Phase": metrics.get(
                    "wyckoff_phase"
                ),
                "Predicted Direction": (
                    predicted_next_direction
                ),
                "Actual Next-Day Direction": (
                    actual_next_direction
                ),
                "Actual 5-Day Direction": (
                    actual_five_day_direction
                ),
                "Next Direction Hit": direction_hit(
                    predicted_next_direction,
                    actual_next_direction,
                ),
                "5D Direction Hit": direction_hit(
                    predicted_next_direction,
                    actual_five_day_direction,
                ),
                "Next-Day Return (%)": next_day_return,
                "5-Day Return (%)": five_day_return,
                "Next Range Lower": projection[
                    "next_day_low"
                ],
                "Next Range Upper": projection[
                    "next_day_high"
                ],
                "Actual Next-Day Low": next_day_low,
                "Actual Next-Day High": next_day_high,
                "Next Range Covered": next_range_covered,
                "Bullish 5D Scenario Level": projection[
                    "bullish_high"
                ],
                "Bearish 5D Scenario Level": projection[
                    "bearish_low"
                ],
                "Actual 5D High": max_high,
                "Actual 5D Low": min_low,
                "Bullish Scenario Hit": bullish_scenario_hit,
                "Bearish Scenario Hit": bearish_scenario_hit,
                "5D Favorable Move (%)": favorable_move,
                "5D Adverse Move (%)": adverse_move,
            }
        )

        completed = (
            test_index
            - start_index
            + 1
        )

        if (
            completed == 1
            or completed % 20 == 0
            or completed == effective_test_days
        ):
            print(
                f"Backtesting: "
                f"{completed}/{effective_test_days} "
                f"completed"
            )

    results_df = pd.DataFrame(results)

    if results_df.empty:
        raise RuntimeError(
            "Backtest produced no valid observations."
        )

    summary_df = build_summary(
        results_df
    )

    run_info_df = pd.DataFrame(
        [
            {
                "Ticker": yahoo_data.ticker,
                "Run Time": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "Completed Daily Bars Available": (
                    len(full_daily_df)
                ),
                "Backtest Observations": len(results_df),
                "Requested Test Days": test_days,
                "Actual Test Days": effective_test_days,
                "Data Rule": (
                    "Completed daily candles only; "
                    "walk-forward, no future data used "
                    "for signal generation."
                ),
                "Model Type": (
                    "Rule-based scenario projector; "
                    "not a guaranteed forecast."
                ),
            }
        ]
    )

    return (
        results_df,
        summary_df,
        run_info_df,
    )


def print_backtest_summary(
    summary_df: pd.DataFrame,
) -> None:
    print()
    print("=" * 112)
    print("PREDICTOR WALK-FORWARD BACKTEST SUMMARY")
    print("=" * 112)

    display_columns = [
        "Score Bucket",
        "Signals",
        "Next-Day Direction Hit Rate (%)",
        "5-Day Direction Hit Rate (%)",
        "Next-Day ATR Range Coverage (%)",
        "Average Next-Day Return (%)",
        "Average 5-Day Return (%)",
        "Average 5D Favorable Move (%)",
        "Average 5D Adverse Move (%)",
    ]

    display_df = summary_df[
        display_columns
    ].copy()

    numeric_columns = [
        "Next-Day Direction Hit Rate (%)",
        "5-Day Direction Hit Rate (%)",
        "Next-Day ATR Range Coverage (%)",
        "Average Next-Day Return (%)",
        "Average 5-Day Return (%)",
        "Average 5D Favorable Move (%)",
        "Average 5D Adverse Move (%)",
    ]

    for column in numeric_columns:
        display_df[column] = display_df[
            column
        ].map(
            lambda value: safe_number(
                value,
                2,
            )
        )

    print(
        display_df.to_string(
            index=False,
        )
    )


def main() -> None:
    print()
    print("=" * 68)
    print("IDX SCENARIO PROJECTOR WALK-FORWARD BACKTEST")
    print("=" * 68)
    print()
    print(
        "This tests historical predictor signals using "
        "completed daily candles only."
    )
    print()

    ticker_input = input(
        "Enter IDX ticker code (example: ISAT): "
    ).strip().upper()

    if not ticker_input:
        print("Ticker code cannot be empty.")
        return

    lookback_input = input(
        "Backtest days [default: 120, max: 250]: "
    ).strip()

    test_days = 120

    if lookback_input:
        try:
            test_days = int(lookback_input)

            if test_days < 20:
                raise ValueError

            if test_days > 250:
                test_days = 250

        except ValueError:
            print(
                "Invalid value. Using default 120 days."
            )

            test_days = 120

    try:
        (
            results_df,
            summary_df,
            run_info_df,
        ) = run_walk_forward_backtest(
            ticker_input,
            test_days,
        )

        quality_filter_df = (
            build_quality_filter_summary(
                results_df
            )
        )

        chronological_df = (
            build_chronological_summary(
                results_df
            )
        )

        generated_at = datetime.now().strftime(
            "%Y%m%d_%H%M"
        )

        ticker_code = ticker_input.replace(
            ".JK",
            "",
        )

        csv_output_path = (
            BACKTEST_OUTPUT_DIR
            / (
                f"{ticker_code}_Predictor_Backtest_"
                f"{generated_at}.csv"
            )
        )

        excel_output_path = (
            BACKTEST_OUTPUT_DIR
            / (
                f"{ticker_code}_Predictor_Backtest_"
                f"{generated_at}.xlsx"
            )
        )

        results_df.to_csv(
            csv_output_path,
            index=False,
        )

        write_excel_output(
            results_df,
            summary_df,
            quality_filter_df,
            chronological_df,
            run_info_df,
            excel_output_path,
        )

        quality_filter_df = (
            build_quality_filter_summary(
                results_df
            )
        )

        chronological_df = (
            build_chronological_summary(
                results_df
            )
        )

        print()
        print("=" * 112)
        print("BULLISH QUALITY-FILTER SUMMARY")
        print("=" * 112)

        print(
            quality_filter_df.to_string(
                index=False,
            )
        )

        if not chronological_df.empty:
            print()
            print("=" * 112)
            print("BULLISH SIGNAL TIME-SPLIT SUMMARY")
            print("=" * 112)

            print(
                chronological_df.to_string(
                    index=False,
                )
            )

        print()
        print("=" * 68)
        print("BACKTEST COMPLETED")
        print("=" * 68)
        print(
            f"Historical observations: {len(results_df)}"
        )
        print()
        print("Generated CSV backtest:")
        print(csv_output_path)
        print()
        print("Generated Excel backtest:")
        print(excel_output_path)

    except Exception as error:
        logger.exception(
            "Predictor backtest failed"
        )

        print()
        print("BACKTEST ERROR")
        print("-" * 68)
        print(error)


if __name__ == "__main__":
    main()