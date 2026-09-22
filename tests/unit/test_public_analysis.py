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


def _loader(history: pd.DataFrame):
    def load(
        ticker: str,
        *,
        as_of: datetime,
        period: str,
        downloader,
    ) -> pd.DataFrame:
        del ticker, as_of, period, downloader
        return history.copy()

    return load


def test_live_analysis_returns_public_price_metrics_and_trade_plan():
    result = analyze_public_ticker(
        "bbca",
        as_of=datetime(2026, 9, 22, 12, tzinfo=_JAKARTA),
        loader=_loader(_history()),
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


def test_live_analysis_is_conservative_without_relative_strength_or_risk_classification():
    result = analyze_public_ticker(
        "BBCA.JK",
        as_of=datetime(2026, 9, 22, 12, tzinfo=_JAKARTA),
        loader=_loader(_history()),
    )

    assert result.relative_strength_available is False
    assert result.risk_category == RiskCategory.UNKNOWN
    assert result.decision.label == DecisionLabel.WAIT
    assert any(
        "Risk classification is unavailable" in reason
        for reason in result.decision.reasons
    )
    assert "IHSG relative strength" in result.data_status


def test_live_analysis_returns_insufficient_data_decision_for_short_history():
    result = analyze_public_ticker(
        "BBCA",
        as_of=datetime(2026, 9, 22, 12, tzinfo=_JAKARTA),
        loader=_loader(_history(rows=49)),
    )

    assert result.decision.label == DecisionLabel.INSUFFICIENT_DATA
    assert result.trade_plan is None
    assert result.latest_close is None
    assert "49 rows available" in result.data_status


def test_live_analysis_detects_extended_price():
    history = _history()
    history.loc[history.index[-1], "Close"] = 2_000.0
    history.loc[history.index[-1], "High"] = 2_010.0
    history.loc[history.index[-1], "Open"] = 1_995.0
    history.loc[history.index[-1], "Low"] = 1_990.0

    result = analyze_public_ticker(
        "BBCA",
        as_of=datetime(2026, 9, 22, 12, tzinfo=_JAKARTA),
        loader=_loader(history),
    )

    assert result.extension_risk is True


def test_live_analysis_wraps_loader_failure():
    def failing_loader(
        ticker: str,
        *,
        as_of: datetime,
        period: str,
        downloader,
    ) -> pd.DataFrame:
        del ticker, as_of, period, downloader
        raise ConnectionError("network unavailable")

    with pytest.raises(
        PublicAnalysisError,
        match="could not load BBCA.JK",
    ):
        analyze_public_ticker(
            "BBCA",
            as_of=datetime(2026, 9, 22, 12, tzinfo=_JAKARTA),
            loader=failing_loader,
        )


def test_live_analysis_returns_defensive_history_copy():
    source_history = _history()

    result = analyze_public_ticker(
        "BBCA",
        as_of=datetime(2026, 9, 22, 12, tzinfo=_JAKARTA),
        loader=_loader(source_history),
    )
    result.history.loc[result.history.index[0], "Close"] = -1.0

    assert source_history["Close"].iloc[0] == 1_000.0