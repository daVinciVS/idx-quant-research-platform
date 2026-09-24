import pandas as pd
from src.analytics.decision import RiskCategory
from src.analytics.public_execution_risk import (
    classify_public_execution_risk,
)


def _history(
    *,
    close: float = 1_000.0,
    volume: float = 2_000_000.0,
    rows: int = 20,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Close": [close] * rows,
            "Volume": [volume] * rows,
        }
    )


def test_safe_when_public_execution_metrics_meet_thresholds():
    result = classify_public_execution_risk(
        _history(close=1_000.0, volume=2_000_000.0),
        atr14=50.0,
        latest_close=1_000.0,
    )

    assert result.category == RiskCategory.SAFE
    assert result.average_traded_value_20d == 2_000_000_000.0
    assert result.atr_percent == 0.05
    assert result.zero_volume_days_20d == 0
    assert result.volume_stability_20d == 1.0


def test_moderate_when_traded_value_is_below_one_billion():
    result = classify_public_execution_risk(
        _history(close=1_000.0, volume=500_000.0),
        atr14=50.0,
        latest_close=1_000.0,
    )

    assert result.category == RiskCategory.MODERATE
    assert "below IDR 1B" in result.reasons[0]


def test_extreme_when_traded_value_is_below_two_hundred_fifty_million():
    result = classify_public_execution_risk(
        _history(close=1_000.0, volume=200_000.0),
        atr14=50.0,
        latest_close=1_000.0,
    )

    assert result.category == RiskCategory.EXTREME
    assert "below IDR 250M" in result.reasons[0]


def test_extreme_when_recent_history_contains_zero_volume():
    history = _history()
    history.loc[history.index[-1], "Volume"] = 0.0

    result = classify_public_execution_risk(
        history,
        atr14=50.0,
        latest_close=1_000.0,
    )

    assert result.category == RiskCategory.EXTREME
    assert "zero-volume" in result.reasons[0]


def test_extreme_when_atr_percent_exceeds_twelve_percent():
    result = classify_public_execution_risk(
        _history(),
        atr14=121.0,
        latest_close=1_000.0,
    )

    assert result.category == RiskCategory.EXTREME
    assert "exceeds 12%" in result.reasons[0]


def test_moderate_when_atr_percent_exceeds_seven_percent():
    result = classify_public_execution_risk(
        _history(),
        atr14=71.0,
        latest_close=1_000.0,
    )

    assert result.category == RiskCategory.MODERATE
    assert "exceeds 7%" in result.reasons[0]


def test_moderate_when_volume_is_unstable():
    history = _history()
    history.loc[history.index[-1], "Volume"] = 200_000_000.0

    result = classify_public_execution_risk(
        history,
        atr14=50.0,
        latest_close=1_000.0,
    )

    assert result.category == RiskCategory.MODERATE
    assert "unstable" in result.reasons[0]


def test_unknown_when_history_is_too_short():
    result = classify_public_execution_risk(
        _history(rows=19),
        atr14=50.0,
        latest_close=1_000.0,
    )

    assert result.category == RiskCategory.UNKNOWN
    assert result.average_traded_value_20d is None


def test_unknown_when_required_columns_are_missing():
    result = classify_public_execution_risk(
        pd.DataFrame({"Close": [1_000.0] * 20}),
        atr14=50.0,
        latest_close=1_000.0,
    )

    assert result.category == RiskCategory.UNKNOWN
    assert "Close and Volume" in result.reasons[0]