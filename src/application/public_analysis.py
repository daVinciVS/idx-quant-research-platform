from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from src.analytics.decision import (
    DecisionInputs,
    RiskCategory,
    TradeDecision,
    evaluate_trade_decision,
)
from src.analytics.public_execution_risk import (
    PublicExecutionRisk,
    classify_public_execution_risk,
)
from src.analytics.trade_plan import TradePlan, calculate_trade_plan
from src.data.yahoo_finance import (
    YahooDownloader,
    load_yahoo_daily_ohlcv_symbol,
    normalize_idx_ticker,
)


class PublicAnalysisError(RuntimeError):
    """Raised when public daily-price analysis cannot be completed."""


HistoryLoader = Callable[..., pd.DataFrame]

_IHSG_SYMBOL = "^JKSE"
_MINIMUM_HISTORY_ROWS = 50
_SIX_MONTH_WINDOW_ROWS = 126
_RESISTANCE_WINDOW_ROWS = 20
_ATR_WINDOW_ROWS = 14
_SMA20_WINDOW_ROWS = 20
_SMA50_WINDOW_ROWS = 50
_RELATIVE_STRENGTH_WINDOW_ROWS = 20
_EXTENSION_THRESHOLD = 1.15


@dataclass(frozen=True)
class PublicAnalysisResult:
    """Public Yahoo daily-OHLCV analysis without broker-flow inputs."""

    ticker: str
    as_of: datetime
    as_of_date: str
    history: pd.DataFrame
    latest_close: float | None
    sma20: float | None
    sma50: float | None
    atr14: float | None
    resistance_20d: float | None
    six_month_high: float | None
    trend_template_passed: bool
    extension_risk: bool
    relative_strength_available: bool
    stock_return_20d: float | None
    ihsg_return_20d: float | None
    relative_strength_spread_20d: float | None
    relative_strength_positive: bool | None
    average_traded_value_20d: float | None
    atr_percent: float | None
    zero_volume_days_20d: int | None
    volume_stability_20d: float | None
    execution_risk_reasons: tuple[str, ...]
    risk_category: RiskCategory
    decision: TradeDecision
    trade_plan: TradePlan | None
    data_status: str


@dataclass(frozen=True)
class _PriceMetrics:
    latest_close: float
    sma20: float
    sma50: float
    atr14: float
    resistance_20d: float
    six_month_high: float
    trend_template_passed: bool
    extension_risk: bool


@dataclass(frozen=True)
class _RelativeStrengthMetrics:
    available: bool
    stock_return_20d: float | None
    ihsg_return_20d: float | None
    spread_20d: float | None
    positive: bool | None


def analyze_public_ticker(
    ticker: str,
    *,
    as_of: datetime,
    period: str = "6mo",
    downloader: YahooDownloader | None = None,
    history_loader: HistoryLoader = load_yahoo_daily_ohlcv_symbol,
) -> PublicAnalysisResult:
    """Analyze public IDX daily OHLCV without broker or portfolio data."""
    normalized_ticker = normalize_idx_ticker(ticker)

    try:
        history = history_loader(
            normalized_ticker,
            as_of=as_of,
            period=period,
            downloader=downloader,
        )
    except Exception as error:
        raise PublicAnalysisError(
            f"Public daily analysis could not load {normalized_ticker}."
        ) from error

    return _build_public_analysis(
        ticker=normalized_ticker,
        as_of=as_of,
        history=history,
        period=period,
        downloader=downloader,
        history_loader=history_loader,
    )


def _build_public_analysis(
    *,
    ticker: str,
    as_of: datetime,
    history: pd.DataFrame,
    period: str,
    downloader: YahooDownloader | None,
    history_loader: HistoryLoader,
) -> PublicAnalysisResult:
    frame = history.copy()

    if len(frame) < _MINIMUM_HISTORY_ROWS:
        return _insufficient_history_result(
            ticker=ticker,
            as_of=as_of,
            history=frame,
        )

    metrics = _calculate_price_metrics(frame)
    execution_risk = classify_public_execution_risk(
        frame,
        atr14=metrics.atr14,
        latest_close=metrics.latest_close,
    )
    trade_plan = _calculate_optional_trade_plan(metrics)
    relative_strength = _load_relative_strength(
        stock_history=frame,
        as_of=as_of,
        period=period,
        downloader=downloader,
        history_loader=history_loader,
    )

    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=True,
            trend_template_passed=metrics.trend_template_passed,
            relative_strength_positive=bool(relative_strength.positive),
            wyckoff_phase="Unavailable from public OHLCV-only analysis",
            extension_risk=metrics.extension_risk,
            risk_reward_ratio=(
                trade_plan.pullback_rrr if trade_plan is not None else None
            ),
            risk_category=execution_risk.category,
        )
    )

    return PublicAnalysisResult(
        ticker=ticker,
        as_of=as_of,
        as_of_date=_latest_date_text(frame),
        history=frame,
        latest_close=metrics.latest_close,
        sma20=metrics.sma20,
        sma50=metrics.sma50,
        atr14=metrics.atr14,
        resistance_20d=metrics.resistance_20d,
        six_month_high=metrics.six_month_high,
        trend_template_passed=metrics.trend_template_passed,
        extension_risk=metrics.extension_risk,
        relative_strength_available=relative_strength.available,
        stock_return_20d=relative_strength.stock_return_20d,
        ihsg_return_20d=relative_strength.ihsg_return_20d,
        relative_strength_spread_20d=relative_strength.spread_20d,
        relative_strength_positive=relative_strength.positive,
        average_traded_value_20d=execution_risk.average_traded_value_20d,
        atr_percent=execution_risk.atr_percent,
        zero_volume_days_20d=execution_risk.zero_volume_days_20d,
        volume_stability_20d=execution_risk.volume_stability_20d,
        execution_risk_reasons=execution_risk.reasons,
        risk_category=execution_risk.category,
        decision=decision,
        trade_plan=trade_plan,
        data_status=_data_status(relative_strength, execution_risk),
    )


def _insufficient_history_result(
    *,
    ticker: str,
    as_of: datetime,
    history: pd.DataFrame,
) -> PublicAnalysisResult:
    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=False,
            trend_template_passed=False,
            relative_strength_positive=False,
            wyckoff_phase="Unavailable",
            extension_risk=False,
            risk_reward_ratio=None,
            risk_category=RiskCategory.UNKNOWN,
        )
    )

    return PublicAnalysisResult(
        ticker=ticker,
        as_of=as_of,
        as_of_date=_latest_date_text(history),
        history=history,
        latest_close=None,
        sma20=None,
        sma50=None,
        atr14=None,
        resistance_20d=None,
        six_month_high=None,
        trend_template_passed=False,
        extension_risk=False,
        relative_strength_available=False,
        stock_return_20d=None,
        ihsg_return_20d=None,
        relative_strength_spread_20d=None,
        relative_strength_positive=None,
        average_traded_value_20d=None,
        atr_percent=None,
        zero_volume_days_20d=None,
        volume_stability_20d=None,
        execution_risk_reasons=(
            "Execution-risk classification is unavailable because stock "
            "history is insufficient.",
        ),
        risk_category=RiskCategory.UNKNOWN,
        decision=decision,
        trade_plan=None,
        data_status=(
            f"Insufficient validated daily history: {len(history)} rows "
            f"available; at least {_MINIMUM_HISTORY_ROWS} are required."
        ),
    )


def _load_relative_strength(
    *,
    stock_history: pd.DataFrame,
    as_of: datetime,
    period: str,
    downloader: YahooDownloader | None,
    history_loader: HistoryLoader,
) -> _RelativeStrengthMetrics:
    try:
        benchmark_history = history_loader(
            _IHSG_SYMBOL,
            as_of=as_of,
            period=period,
            downloader=downloader,
        )
    except Exception:
        return _unavailable_relative_strength()

    return _calculate_relative_strength(
        stock_history=stock_history,
        benchmark_history=benchmark_history,
    )


def _calculate_relative_strength(
    *,
    stock_history: pd.DataFrame,
    benchmark_history: pd.DataFrame,
) -> _RelativeStrengthMetrics:
    stock = stock_history.loc[:, ["Date", "Close"]].copy()
    benchmark = benchmark_history.loc[:, ["Date", "Close"]].copy()

    stock["Date"] = pd.to_datetime(stock["Date"])
    benchmark["Date"] = pd.to_datetime(benchmark["Date"])

    aligned = stock.merge(
        benchmark,
        on="Date",
        how="inner",
        suffixes=("_stock", "_ihsg"),
    ).sort_values("Date")

    if len(aligned) <= _RELATIVE_STRENGTH_WINDOW_ROWS:
        return _unavailable_relative_strength()

    start = aligned.iloc[-(_RELATIVE_STRENGTH_WINDOW_ROWS + 1)]
    end = aligned.iloc[-1]

    stock_start = float(start["Close_stock"])
    stock_end = float(end["Close_stock"])
    ihsg_start = float(start["Close_ihsg"])
    ihsg_end = float(end["Close_ihsg"])

    if min(stock_start, stock_end, ihsg_start, ihsg_end) <= 0:
        return _unavailable_relative_strength()

    stock_return = (stock_end / stock_start) - 1.0
    ihsg_return = (ihsg_end / ihsg_start) - 1.0
    spread = stock_return - ihsg_return

    return _RelativeStrengthMetrics(
        available=True,
        stock_return_20d=stock_return,
        ihsg_return_20d=ihsg_return,
        spread_20d=spread,
        positive=spread > 0,
    )


def _unavailable_relative_strength() -> _RelativeStrengthMetrics:
    return _RelativeStrengthMetrics(
        available=False,
        stock_return_20d=None,
        ihsg_return_20d=None,
        spread_20d=None,
        positive=None,
    )


def _data_status(
    relative_strength: _RelativeStrengthMetrics,
    execution_risk: PublicExecutionRisk,
) -> str:
    relative_strength_status = (
        "with 20-day relative strength versus IHSG"
        if relative_strength.available
        else "without an available IHSG relative-strength comparison"
    )

    return (
        f"Validated public daily OHLCV {relative_strength_status}. "
        "Public OHLCV execution-risk classification: "
        f"{execution_risk.category.value}. "
        "Broker flow is not included."
    )


def _calculate_price_metrics(frame: pd.DataFrame) -> _PriceMetrics:
    close = frame["Close"].astype(float)
    high = frame["High"].astype(float)
    low = frame["Low"].astype(float)

    latest_close = float(close.iloc[-1])
    sma20 = float(close.tail(_SMA20_WINDOW_ROWS).mean())
    sma50 = float(close.tail(_SMA50_WINDOW_ROWS).mean())
    atr14 = _calculate_atr14(high=high, low=low, close=close)
    resistance_20d = float(high.tail(_RESISTANCE_WINDOW_ROWS).max())
    six_month_high = float(high.tail(_SIX_MONTH_WINDOW_ROWS).max())

    trend_template_passed = (
        latest_close > sma20
        and latest_close > sma50
        and sma20 > sma50
    )
    extension_risk = latest_close > sma20 * _EXTENSION_THRESHOLD

    return _PriceMetrics(
        latest_close=latest_close,
        sma20=sma20,
        sma50=sma50,
        atr14=atr14,
        resistance_20d=resistance_20d,
        six_month_high=six_month_high,
        trend_template_passed=trend_template_passed,
        extension_risk=extension_risk,
    )


def _calculate_atr14(
    *,
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
) -> float:
    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr14 = true_range.tail(_ATR_WINDOW_ROWS).mean()

    if pd.isna(atr14) or float(atr14) <= 0:
        raise PublicAnalysisError(
            "Public daily history does not contain a usable ATR14."
        )

    return float(atr14)


def _calculate_optional_trade_plan(
    metrics: _PriceMetrics,
) -> TradePlan | None:
    try:
        return calculate_trade_plan(
            close=metrics.latest_close,
            atr14=metrics.atr14,
            resistance=metrics.resistance_20d,
            six_month_high=metrics.six_month_high,
        )
    except (TypeError, ValueError):
        return None


def _latest_date_text(frame: pd.DataFrame) -> str:
    if frame.empty or "Date" not in frame.columns:
        return "Unavailable"

    latest_date = pd.to_datetime(frame["Date"].iloc[-1], errors="coerce")
    if pd.isna(latest_date):
        return "Unavailable"

    return latest_date.date().isoformat()