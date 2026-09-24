from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest
from src.analytics.decision import DecisionLabel, RiskCategory
from src.application.public_analysis import (
    PublicAnalysisError,
    analyze_public_ticker,
)

_JAKARTA = ZoneInfo("Asia/Jakarta")
_AS_OF = datetime(2026, 9, 22, 12, tzinfo=_JAKARTA)


def _history(
    *,
    rows: int = 60,
    start_close: float = 1_000.0,
    daily_change: float = 5.0,
) -> pd.DataFrame:
    dates = pd.bdate_range("2026-06-01", periods=rows)
    close = [
        start_close + (daily_change * offset)
        for offset in range(rows)
    ]

    return pd.DataFrame(
        {
            "Date": dates,
            "Open": [value - 2.0 for value in close],
            "High": [value + 10.0 for value in close],
            "Low": [value - 10.0 for value in close],
            "Close": close,
            "Volume": [1_000_000] * rows,
        }
    )


def _history_loader(histories: dict[str, pd.DataFrame]):
    def load(
        symbol: str,
        *,
        as_of: datetime,
        period: str,
        downloader,
    ) -> pd.DataFrame:
        del as_of, period, downloader

        if symbol not in histories:
            raise ConnectionError(f"No fake history for {symbol}.")

        return histories[symbol].copy()

    return load


def _analyze(
    stock_history: pd.DataFrame,
    *,
    benchmark_history: pd.DataFrame | None = None,
):
    histories = {"BBCA.JK": stock_history}
    if benchmark_history is not None:
        histories["^JKSE"] = benchmark_history

    return analyze_public_ticker(
        "BBCA",
        as_of=_AS_OF,
        history_loader=_history_loader(histories),
    )


def test_live_analysis_returns_public_price_metrics_and_trade_plan():
    result = _analyze(
        _history(),
        benchmark_history=_history(
            start_close=7_000.0,
            daily_change=2.0,
        ),
    )

    assert result.ticker == "BBCA.JK"
    assert result.as_of_date == "2026-08-21"
    assert len(result.history) == 60
    assert result.latest_close == 1_295.0
    assert result.sma20 is not None
    assert result.sma50 is not None
    assert result.atr14 is not None
    assert result.resistance_20d is not None
    assert result.six_month_high is not None
    assert result.trade_plan is not None
    assert result.trend_template_passed is True


def test_live_analysis_calculates_positive_relative_strength_against_ihsg():
    result = _analyze(
        _history(daily_change=10.0),
        benchmark_history=_history(
            start_close=7_000.0,
            daily_change=2.0,
        ),
    )

    assert result.relative_strength_available is True
    assert result.stock_return_20d is not None
    assert result.ihsg_return_20d is not None
    assert result.relative_strength_spread_20d is not None
    assert result.relative_strength_positive is True
    assert result.relative_strength_spread_20d > 0
    assert "relative strength versus IHSG" in result.data_status


def test_live_analysis_calculates_negative_relative_strength_against_ihsg():
    result = _analyze(
        _history(daily_change=1.0),
        benchmark_history=_history(
            start_close=7_000.0,
            daily_change=20.0,
        ),
    )

    assert result.relative_strength_available is True
    assert result.relative_strength_positive is False
    assert result.relative_strength_spread_20d is not None
    assert result.relative_strength_spread_20d < 0


def test_live_analysis_classifies_safe_execution_conditions():
    result = _analyze(
        _history(),
        benchmark_history=_history(
            start_close=7_000.0,
            daily_change=2.0,
        ),
    )

    assert result.risk_category == RiskCategory.SAFE
    assert result.average_traded_value_20d is not None
    assert result.atr_percent is not None
    assert result.zero_volume_days_20d == 0
    assert result.volume_stability_20d is not None
    assert result.execution_risk_reasons


def test_live_analysis_keeps_stock_result_when_ihsg_is_unavailable():
    result = _analyze(_history())

    assert result.relative_strength_available is False
    assert result.stock_return_20d is None
    assert result.ihsg_return_20d is None
    assert result.relative_strength_spread_20d is None
    assert result.relative_strength_positive is None
    assert "without an available IHSG relative-strength comparison" in (
        result.data_status
    )


def test_live_analysis_returns_insufficient_data_for_short_stock_history():
    result = _analyze(
        _history(rows=49),
        benchmark_history=_history(),
    )

    assert result.decision.label == DecisionLabel.INSUFFICIENT_DATA
    assert result.trade_plan is None
    assert result.latest_close is None
    assert result.relative_strength_available is False
    assert "49 rows available" in result.data_status
    assert result.risk_category == RiskCategory.UNKNOWN
    assert result.average_traded_value_20d is None
    assert result.execution_risk_reasons


def test_live_analysis_detects_extended_price():
    history = _history()
    history.loc[history.index[-1], "Close"] = 2_000.0
    history.loc[history.index[-1], "High"] = 2_010.0
    history.loc[history.index[-1], "Open"] = 1_995.0
    history.loc[history.index[-1], "Low"] = 1_990.0

    result = _analyze(
        history,
        benchmark_history=_history(
            start_close=7_000.0,
            daily_change=2.0,
        ),
    )

    assert result.extension_risk is True


def test_live_analysis_wraps_stock_loader_failure():
    def failing_loader(
        symbol: str,
        *,
        as_of: datetime,
        period: str,
        downloader,
    ) -> pd.DataFrame:
        del symbol, as_of, period, downloader
        raise ConnectionError("network unavailable")

    with pytest.raises(
        PublicAnalysisError,
        match="could not load BBCA.JK",
    ):
        analyze_public_ticker(
            "BBCA",
            as_of=_AS_OF,
            history_loader=failing_loader,
        )


def test_live_analysis_returns_defensive_history_copy():
    source_history = _history()
    benchmark_history = _history(
        start_close=7_000.0,
        daily_change=2.0,
    )

    result = _analyze(
        source_history,
        benchmark_history=benchmark_history,
    )
    result.history.loc[result.history.index[0], "Close"] = -1.0

    assert source_history["Close"].iloc[0] == 1_000.0

def test_live_analysis_avoids_zero_volume_execution_conditions():
    history = _history()
    history.loc[history.index[-1], "Volume"] = 0

    result = _analyze(
        history,
        benchmark_history=_history(
            start_close=7_000.0,
            daily_change=2.0,
        ),
    )

    assert result.risk_category == RiskCategory.EXTREME
    assert result.decision.label == DecisionLabel.AVOID
    assert result.zero_volume_days_20d == 1
    assert any(
        "zero-volume" in reason
        for reason in result.execution_risk_reasons
    )

def test_live_analysis_watchlists_moderate_execution_conditions():
    history = _history()
    history["Volume"] = 500_000.0

    result = _analyze(
        history,
        benchmark_history=_history(
            start_close=7_000.0,
            daily_change=2.0,
        ),
    )

    assert result.risk_category == RiskCategory.MODERATE
    assert result.decision.label == DecisionLabel.WATCHLIST