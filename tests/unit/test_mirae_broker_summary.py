from datetime import date
from pathlib import Path

import pytest
from src.data.mirae_broker_summary import (
    MiraeBrokerSummaryError,
    load_mirae_broker_summary,
)

_FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_loader_aggregates_paired_mirae_rows_by_broker():
    result = load_mirae_broker_summary(
        _FIXTURES_DIR / "mirae_broker_summary_valid.csv",
        ticker="mdia.jk",
        start_date=date(2026, 9, 18),
        end_date=date(2026, 9, 19),
        region="ALL",
    )

    activities = {
        activity.broker_code: activity
        for activity in result.activities
    }

    yu = activities["YU"]
    assert yu.buy_value == pytest.approx(120_000_000_000.0)
    assert yu.sell_value == 0.0
    assert yu.buy_average_price == pytest.approx(
        (
            (91_660_000_000 * 197)
            + (18_340_000_000 * 199)
            + (10_000_000_000 * 200)
        )
        / 120_000_000_000
    )
    assert yu.buy_frequency == 0
    assert yu.buy_volume == 0

    ss = activities["SS"]
    assert ss.buy_value == 0.0
    assert ss.sell_value == pytest.approx(79_670_000_000.0)
    assert ss.sell_average_price == pytest.approx(
        (
            (74_670_000_000 * 200)
            + (5_000_000_000 * 202)
        )
        / 79_670_000_000
    )

    assert result.metadata.ticker == "MDIA"
    assert result.metadata.investor == "all"
    assert result.metadata.source == "mirae_manual"
    assert result.metadata.market == "ALL"


def test_loader_filters_by_selected_date_range():
    result = load_mirae_broker_summary(
        _FIXTURES_DIR / "mirae_broker_summary_valid.csv",
        ticker="MDIA",
        start_date=date(2026, 9, 19),
        end_date=date(2026, 9, 19),
        region="all",
    )

    activities = {
        activity.broker_code: activity
        for activity in result.activities
    }

    assert set(activities) == {"AK", "CC", "SS", "YU"}
    assert activities["YU"].buy_value == 10_000_000_000.0
    assert activities["SS"].sell_value == 5_000_000_000.0


def test_loader_returns_empty_result_for_no_matching_rows():
    result = load_mirae_broker_summary(
        _FIXTURES_DIR / "mirae_broker_summary_valid.csv",
        ticker="BBCA",
        start_date=date(2026, 9, 18),
        end_date=date(2026, 9, 19),
        region="all",
    )

    assert result.activities == ()
    assert result.metadata.ticker == "BBCA"


def test_loader_rejects_missing_required_columns():
    with pytest.raises(
        MiraeBrokerSummaryError,
        match="missing columns: Sell_Average_Price",
    ):
        load_mirae_broker_summary(
            _FIXTURES_DIR / "mirae_broker_summary_missing_column.csv",
            ticker="MDIA",
            start_date=date(2026, 9, 18),
            end_date=date(2026, 9, 18),
            region="all",
        )


@pytest.mark.parametrize("region", ["", "institutional", "foreigners"])
def test_loader_rejects_unknown_region(region):
    with pytest.raises(
        MiraeBrokerSummaryError,
        match="Region must be one of",
    ):
        load_mirae_broker_summary(
            _FIXTURES_DIR / "mirae_broker_summary_valid.csv",
            ticker="MDIA",
            start_date=date(2026, 9, 18),
            end_date=date(2026, 9, 18),
            region=region,
        )


def test_loader_rejects_inverted_date_range():
    with pytest.raises(
        MiraeBrokerSummaryError,
        match="start_date must be on or before end_date",
    ):
        load_mirae_broker_summary(
            _FIXTURES_DIR / "mirae_broker_summary_valid.csv",
            ticker="MDIA",
            start_date=date(2026, 9, 19),
            end_date=date(2026, 9, 18),
            region="all",
        )