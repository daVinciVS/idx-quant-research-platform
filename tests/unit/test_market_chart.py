import pandas as pd
from src.analytics.trade_plan import calculate_trade_plan
from src.application.demo_market_data import load_demo_ohlcv
from src.presentation.market_chart import (
    build_demo_market_chart,
    prepare_market_chart_data,
)


def test_prepare_market_chart_data_adds_moving_averages():
    frame = load_demo_ohlcv("demo_entry_setup")

    chart_data = prepare_market_chart_data(frame)

    assert len(chart_data) == 100
    assert list(chart_data.columns) == [
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "SMA20",
        "SMA50",
    ]
    assert chart_data["Date"].is_monotonic_increasing
    assert chart_data["SMA20"].iloc[:19].isna().all()
    assert chart_data["SMA20"].iloc[19] > 0
    assert chart_data["SMA50"].iloc[:49].isna().all()
    assert chart_data["SMA50"].iloc[49] > 0


def test_market_chart_builds_from_valid_fixture_and_trade_plan():
    frame = load_demo_ohlcv("demo_entry_setup")
    trade_plan = calculate_trade_plan(
        close=1_000.0,
        atr14=50.0,
        resistance=1_100.0,
        six_month_high=1_200.0,
    )

    chart = build_demo_market_chart(frame, trade_plan)
    specification = chart.to_dict()

    assert specification["vconcat"][0]["height"] == 420
    assert specification["vconcat"][1]["height"] == 110
    assert len(specification["vconcat"][0]["layer"]) == 6
    assert "Synthetic OHLCV fixture" in specification["vconcat"][0]["title"]["text"]


def test_prepare_market_chart_data_does_not_mutate_source_frame():
    source = pd.DataFrame(
        {
            "Date": pd.date_range("2026-01-01", periods=80, freq="B"),
            "Open": [1_000.0] * 80,
            "High": [1_010.0] * 80,
            "Low": [990.0] * 80,
            "Close": [1_005.0] * 80,
            "Volume": [1_000_000] * 80,
        }
    )

    chart_data = prepare_market_chart_data(source)

    assert "SMA20" not in source.columns
    assert "SMA50" not in source.columns
    assert "SMA20" in chart_data.columns
    assert "SMA50" in chart_data.columns

def test_market_chart_uses_full_number_price_axis_format():
    frame = load_demo_ohlcv("demo_entry_setup")
    trade_plan = calculate_trade_plan(
        close=1_000.0,
        atr14=50.0,
        resistance=1_100.0,
        six_month_high=1_200.0,
    )

    chart = build_demo_market_chart(frame, trade_plan)
    specification = chart.to_dict()

    price_axis = specification["vconcat"][0]["layer"][0]["encoding"]["y"]["axis"]

    assert price_axis["format"] == ",.0f"