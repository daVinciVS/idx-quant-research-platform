from pathlib import Path

import pandas as pd
import pytest
from src.application.demo_market_data import (
    _validate_demo_ohlcv,
    load_demo_case_ohlcv,
    load_demo_ohlcv,
)


def test_demo_entry_fixture_loads_valid_ohlcv_data():
    frame = load_demo_ohlcv("demo_entry_setup")

    assert list(frame.columns) == [
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]
    assert len(frame) >= 80
    assert pd.api.types.is_datetime64_any_dtype(frame["Date"])
    assert frame["Date"].is_monotonic_increasing
    assert (frame[["Open", "High", "Low", "Close"]] > 0).all().all()
    assert (frame["Volume"] >= 0).all()


def test_loader_rejects_unknown_fixture_name():
    with pytest.raises(ValueError, match="No public market-data fixture"):
        load_demo_ohlcv("unknown_case")


def test_validator_rejects_too_short_fixture():
    frame = pd.DataFrame(
        {
            "Date": pd.date_range("2026-01-01", periods=2, freq="B"),
            "Open": [1_000, 1_001],
            "High": [1_005, 1_006],
            "Low": [995, 996],
            "Close": [1_002, 1_003],
            "Volume": [1_000, 1_100],
        }
    )

    with pytest.raises(ValueError, match="at least 80 rows"):
        _validate_demo_ohlcv(frame, case_id="too_short")


def test_validator_rejects_invalid_price_range():
    frame = pd.DataFrame(
        {
            "Date": pd.date_range("2026-01-01", periods=80, freq="B"),
            "Open": [1_000.0] * 80,
            "High": [900.0] * 80,
            "Low": [950.0] * 80,
            "Close": [1_000.0] * 80,
            "Volume": [1_000.0] * 80,
        }
    )

    with pytest.raises(ValueError, match="invalid high price"):
        _validate_demo_ohlcv(frame, case_id="invalid_range")


def test_fixture_path_is_public_demo_data():
    module_path = Path(__file__).resolve().parents[2]
    expected_path = module_path / "data" / "demo" / "market_data"

    assert expected_path.exists()

@pytest.mark.parametrize(
    "case_id",
    ["consider_entry", "reduced_size"],
)
def test_entry_eligible_demo_cases_have_market_data(case_id):
    frame = load_demo_case_ohlcv(case_id)

    assert frame is not None
    assert len(frame) == 100
    assert frame["Date"].is_monotonic_increasing


@pytest.mark.parametrize(
    "case_id",
    ["avoid", "watchlist", "insufficient_data"],
)
def test_cases_without_market_fixture_return_none(case_id):
    assert load_demo_case_ohlcv(case_id) is None