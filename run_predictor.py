from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


try:
    from __main__ import (
        AnalyticsEngine,
        StockDataFetcher,
        logger,
    )

except ImportError:
    from generate_report import (
        AnalyticsEngine,
        StockDataFetcher,
        logger,
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


def safe_flag(value: Any) -> bool:
    try:
        if pd.isna(value):
            return False

        return bool(value)

    except (TypeError, ValueError):
        return False


def six_month_window(
    analyzed_df: pd.DataFrame,
) -> pd.DataFrame:
    latest_date = pd.to_datetime(
        analyzed_df["Date"].max()
    )

    six_month_cutoff = latest_date - pd.DateOffset(
        months=6,
    )

    return analyzed_df[
        analyzed_df["Date"] >= six_month_cutoff
    ].copy()


def calculate_projection_signals(
    metrics: dict[str, Any],
) -> tuple[int, list[tuple[str, str, int]]]:
    score = 0
    signals: list[tuple[str, str, int]] = []

    latest_close = numeric_value(
        metrics.get("latest_close")
    )

    sma20 = numeric_value(
        metrics.get("sma20")
    )

    sma50 = numeric_value(
        metrics.get("sma50")
    )

    macd_histogram = numeric_value(
        metrics.get("macd_histogram")
    )

    rsi14 = numeric_value(
        metrics.get("rsi14")
    )

    adx14 = numeric_value(
        metrics.get("adx14")
    )

    plus_di = numeric_value(
        metrics.get("plus_di")
    )

    minus_di = numeric_value(
        metrics.get("minus_di")
    )

    volume_ratio = numeric_value(
        metrics.get("volume_ratio")
    )

    extension_status = str(
        metrics.get(
            "extension_risk_status",
            "",
        )
    ).upper()

    if (
        pd.notna(latest_close)
        and pd.notna(sma20)
        and latest_close > sma20
    ):
        score += 1
        signals.append(
            (
                "Price vs SMA20",
                "Bullish",
                1,
            )
        )

    elif (
        pd.notna(latest_close)
        and pd.notna(sma20)
        and latest_close < sma20
    ):
        score -= 1
        signals.append(
            (
                "Price vs SMA20",
                "Bearish",
                -1,
            )
        )

    if (
        pd.notna(sma20)
        and pd.notna(sma50)
        and sma20 > sma50
    ):
        score += 1
        signals.append(
            (
                "SMA20 vs SMA50",
                "Bullish alignment",
                1,
            )
        )

    elif (
        pd.notna(sma20)
        and pd.notna(sma50)
        and sma20 < sma50
    ):
        score -= 1
        signals.append(
            (
                "SMA20 vs SMA50",
                "Bearish alignment",
                -1,
            )
        )

    if pd.notna(macd_histogram):
        if macd_histogram > 0:
            score += 1
            signals.append(
                (
                    "MACD Histogram",
                    "Positive momentum",
                    1,
                )
            )

        elif macd_histogram < 0:
            score -= 1
            signals.append(
                (
                    "MACD Histogram",
                    "Negative momentum",
                    -1,
                )
            )

    if pd.notna(rsi14):
        if 50 <= rsi14 <= 70:
            score += 1
            signals.append(
                (
                    "RSI14",
                    f"Constructive ({rsi14:.1f})",
                    1,
                )
            )

        elif rsi14 < 45:
            score -= 1
            signals.append(
                (
                    "RSI14",
                    f"Weak ({rsi14:.1f})",
                    -1,
                )
            )

        elif rsi14 > 75:
            score -= 1
            signals.append(
                (
                    "RSI14",
                    f"Overbought ({rsi14:.1f})",
                    -1,
                )
            )

    if (
        pd.notna(adx14)
        and pd.notna(plus_di)
        and pd.notna(minus_di)
        and adx14 >= 20
    ):
        if plus_di > minus_di:
            score += 1
            signals.append(
                (
                    "ADX / DI",
                    "Positive trend pressure",
                    1,
                )
            )

        elif minus_di > plus_di:
            score -= 1
            signals.append(
                (
                    "ADX / DI",
                    "Negative trend pressure",
                    -1,
                )
            )

    if (
        pd.notna(volume_ratio)
        and volume_ratio >= 1.20
        and safe_flag(
            metrics.get(
                "institutional_accumulation_flag"
            )
        )
    ):
        score += 1
        signals.append(
            (
                "Volume Context",
                "Bullish volume confirmation",
                1,
            )
        )

    elif safe_flag(
        metrics.get(
            "distribution_pressure_flag"
        )
    ):
        score -= 1
        signals.append(
            (
                "Volume Context",
                "Distribution pressure",
                -1,
            )
        )

    if metrics.get("minervini_passed"):
        score += 1
        signals.append(
            (
                "Minervini",
                "Trend template passed",
                1,
            )
        )

    elif metrics.get("minervini_passed") is False:
        score -= 1
        signals.append(
            (
                "Minervini",
                "Trend template failed",
                -1,
            )
        )

    if "BUYING CLIMAX" in extension_status:
        score -= 2
        signals.append(
            (
                "Extension Risk",
                "Buying climax / severely extended",
                -2,
            )
        )

    elif "EXTENDED" in extension_status:
        score -= 1
        signals.append(
            (
                "Extension Risk",
                "Extended; avoid chasing",
                -1,
            )
        )

    return score, signals


def classify_projection_bias(
    signal_score: int,
    metrics: dict[str, Any],
) -> tuple[str, str]:
    extension_status = str(
        metrics.get(
            "extension_risk_status",
            "",
        )
    ).upper()

    minervini_passed = bool(
        metrics.get("minervini_passed")
    )

    if "BUYING CLIMAX" in extension_status:
        return (
            "EXTENDED / HIGH PULLBACK RISK",
            "Low",
        )

    if not minervini_passed:
        if signal_score >= 4:
            return (
                "SHORT-TERM BULLISH MOMENTUM — "
                "LONG-TERM TREND UNQUALIFIED",
                "Low",
            )

        if signal_score >= 1:
            return (
                "SHORT-TERM RECOVERY ATTEMPT — "
                "LONG-TERM TREND UNQUALIFIED",
                "Low",
            )

        if signal_score <= -4:
            return (
                "BEARISH STRUCTURE — "
                "LONG-TERM TREND UNQUALIFIED",
                "Moderate",
            )

        return (
            "NEUTRAL / TRANSITION — "
            "LONG-TERM TREND UNQUALIFIED",
            "Low",
        )

    if signal_score >= 4:
        return (
            "BULLISH CONTINUATION BIAS",
            "Moderate",
        )

    if signal_score >= 1:
        return (
            "MILDLY BULLISH / CONSOLIDATION BIAS",
            "Low to Moderate",
        )

    if signal_score <= -4:
        return (
            "BEARISH PULLBACK BIAS",
            "Moderate",
        )

    if signal_score <= -1:
        return (
            "MILDLY BEARISH / RANGE BIAS",
            "Low to Moderate",
        )

    return (
        "NEUTRAL / RANGE BIAS",
        "Low",
    )


def calculate_scenarios(
    latest_close: float,
    atr14: float,
    signal_score: int,
) -> dict[str, float]:
    next_day_range = atr14
    five_day_range = atr14 * math.sqrt(5)

    next_day_low = latest_close - next_day_range
    next_day_high = latest_close + next_day_range

    if signal_score >= 4:
        base_case = latest_close + (
            0.60 * five_day_range
        )
        bullish_high = latest_close + (
            1.40 * five_day_range
        )
        bearish_low = latest_close - (
            0.70 * five_day_range
        )

    elif signal_score >= 1:
        base_case = latest_close + (
            0.25 * five_day_range
        )
        bullish_high = latest_close + (
            1.00 * five_day_range
        )
        bearish_low = latest_close - (
            0.90 * five_day_range
        )

    elif signal_score <= -4:
        base_case = latest_close - (
            0.60 * five_day_range
        )
        bullish_high = latest_close + (
            0.70 * five_day_range
        )
        bearish_low = latest_close - (
            1.40 * five_day_range
        )

    elif signal_score <= -1:
        base_case = latest_close - (
            0.25 * five_day_range
        )
        bullish_high = latest_close + (
            0.90 * five_day_range
        )
        bearish_low = latest_close - (
            1.00 * five_day_range
        )

    else:
        base_case = latest_close
        bullish_high = latest_close + (
            1.00 * five_day_range
        )
        bearish_low = latest_close - (
            1.00 * five_day_range
        )

    return {
        "next_day_low": max(next_day_low, 0),
        "next_day_high": next_day_high,
        "base_case": max(base_case, 0),
        "bullish_high": bullish_high,
        "bearish_low": max(bearish_low, 0),
    }


def print_projection(
    ticker: str,
    metrics: dict[str, Any],
    signal_score: int,
    signals: list[tuple[str, str, int]],
) -> None:
    latest_date = pd.to_datetime(
        metrics["latest_date"]
    )

    latest_close = numeric_value(
        metrics.get("latest_close")
    )

    atr14 = numeric_value(
        metrics.get("atr14")
    )

    bias, confidence = classify_projection_bias(
        signal_score,
        metrics,
    )

    print()
    print("=" * 68)
    print("IDX NEXT-SESSION & 5-SESSION SCENARIO PROJECTOR")
    print("=" * 68)
    print()
    print(f"Ticker: {ticker}")
    print(
        "Forecast based on completed session: "
        f"{latest_date.strftime('%d %b %Y')}"
    )
    print(
        "Projection horizon: next trading session "
        "and next five trading sessions"
    )
    print()

    print("MODEL OUTPUT")
    print("-" * 68)
    print(f"Directional Bias: {bias}")
    print(f"Signal Score: {signal_score:+d}")
    print(f"Confidence: {confidence}")
    print(
        "Long-Term Eligibility: "
        + (
            "QUALIFIED"
            if metrics.get("minervini_passed")
            else "NOT QUALIFIED"
        )
    )
    print(
        "Current Completed Close: "
        f"Rp {safe_number(latest_close)}"
    )
    print(
        "ATR14: "
        f"Rp {safe_number(atr14)}"
    )
    print()

    if pd.notna(latest_close) and pd.notna(atr14):
        scenarios = calculate_scenarios(
            latest_close,
            atr14,
            signal_score,
        )

        print("NEXT-SESSION EXPECTED RANGE")
        print("-" * 68)
        print(
            "ATR-Based Lower Range: "
            f"Rp {safe_number(scenarios['next_day_low'])}"
        )
        print(
            "ATR-Based Upper Range: "
            f"Rp {safe_number(scenarios['next_day_high'])}"
        )
        print()

        print("FIVE-SESSION SCENARIOS")
        print("-" * 68)
        print(
            "Bullish continuation upper range: "
            f"Rp {safe_number(scenarios['bullish_high'])}"
        )
        print(
            "Base-case reference level: "
            f"Rp {safe_number(scenarios['base_case'])}"
        )
        print(
            "Bearish pullback lower range: "
            f"Rp {safe_number(scenarios['bearish_low'])}"
        )
        print()

    print("KEY TECHNICAL LEVELS")
    print("-" * 68)
    print(
        "SMA20: "
        f"Rp {safe_number(metrics.get('sma20'))}"
    )
    print(
        "SMA50: "
        f"Rp {safe_number(metrics.get('sma50'))}"
    )
    print(
        "Support 20D: "
        f"Rp {safe_number(metrics.get('support'))}"
    )
    print(
        "Breakout Trigger: "
        f"Rp {safe_number(metrics.get('breakout_entry'))}"
    )
    print(
        "Pullback Stop Loss: "
        f"Rp {safe_number(metrics.get('pullback_stop_loss'))}"
    )
    print()

    print("SIGNAL COMPONENTS")
    print("-" * 68)

    for signal_name, signal_text, points in signals:
        print(
            f"{points:+d} | "
            f"{signal_name}: {signal_text}"
        )

    print()
    print("MODEL DISCLOSURE")
    print("-" * 68)
    print(
        "This is a rule-based technical scenario model, "
        "not a guaranteed price forecast."
    )
    print(
        "It uses completed daily candles only and does not "
        "use the current intraday candle."
    )
    print(
        "Validate liquidity, news, corporate actions, "
        "market conditions, and position risk before acting."
    )


def main() -> None:
    print()
    print("=" * 68)
    print("IDX NEXT-SESSION & 5-SESSION SCENARIO PROJECTOR")
    print("=" * 68)
    print()
    print(
        "This tool uses completed daily candles only."
    )
    print()

    ticker_input = input(
        "Enter IDX ticker code (example: ISAT): "
    ).strip().upper()

    if not ticker_input:
        print("Ticker code cannot be empty.")
        return

    try:
        fetcher = StockDataFetcher()
        analytics = AnalyticsEngine()

        yahoo_data = fetcher.fetch_yahoo_data(
            ticker_input,
            period="2y",
        )

        analyzed_df = analytics.calculate_indicators(
            yahoo_data.daily_price,
            yahoo_data.benchmark_price,
            pd.DataFrame(),
        )

        report_df = six_month_window(
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

        signal_score, signals = (
            calculate_projection_signals(
                metrics
            )
        )

        print_projection(
            yahoo_data.ticker,
            metrics,
            signal_score,
            signals,
        )

    except Exception as error:
        logger.exception(
            "Scenario projection failed"
        )

        print()
        print("PREDICTOR ERROR")
        print("-" * 68)
        print(error)


if __name__ == "__main__":
    main()