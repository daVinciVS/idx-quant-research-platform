from datetime import date

import pytest
from src.application.broker_analytics import (
    calculate_price_distance_pct,
    rank_top_net_buyers,
    rank_top_net_sellers,
    summarize_top_net_buyer_context,
)
from src.domain.broker_summary import (
    BrokerActivity,
    BrokerSummaryMetadata,
    BrokerSummaryResult,
)


@pytest.fixture
def broker_activities() -> tuple[BrokerActivity, ...]:
    return (
        BrokerActivity(
            broker_code="SQ",
            buy_frequency=120,
            buy_volume=26_837_300,
            buy_value=185_357_180_000.0,
            sell_frequency=10,
            sell_volume=1_493_000,
            sell_value=10_374_017_500.0,
            buy_average_price=6_906.70,
            sell_average_price=6_919.24,
        ),
        BrokerActivity(
            broker_code="AB",
            buy_frequency=25,
            buy_volume=2_000_000,
            buy_value=13_000_000_000.0,
            sell_frequency=145,
            sell_volume=20_000_000,
            sell_value=132_000_000_000.0,
            buy_average_price=6_500.0,
            sell_average_price=6_600.0,
        ),
        BrokerActivity(
            broker_code="CC",
            buy_frequency=50,
            buy_volume=5_000_000,
            buy_value=34_000_000_000.0,
            sell_frequency=50,
            sell_volume=5_000_000,
            sell_value=34_000_000_000.0,
            buy_average_price=6_800.0,
            sell_average_price=6_800.0,
        ),
    )


def test_broker_activity_calculates_net_volume_and_value():
    activity = BrokerActivity(
        broker_code="SQ",
        buy_frequency=10,
        buy_volume=100,
        buy_value=1_000_000.0,
        sell_frequency=5,
        sell_volume=40,
        sell_value=500_000.0,
        buy_average_price=10_000.0,
        sell_average_price=12_500.0,
    )

    assert activity.net_volume == 60
    assert activity.net_value == 500_000.0


def test_rank_top_net_buyers_excludes_non_positive_net_value(
    broker_activities,
):
    ranked = rank_top_net_buyers(broker_activities)

    assert [activity.broker_code for activity in ranked] == ["SQ"]


def test_rank_top_net_sellers_excludes_non_negative_net_value(
    broker_activities,
):
    ranked = rank_top_net_sellers(broker_activities)

    assert [activity.broker_code for activity in ranked] == ["AB"]


def test_rank_top_net_buyers_respects_limit(broker_activities):
    ranked = rank_top_net_buyers(broker_activities, limit=1)

    assert len(ranked) == 1
    assert ranked[0].broker_code == "SQ"


@pytest.mark.parametrize("limit", [0, -1])
def test_rankers_reject_invalid_limit(limit, broker_activities):
    with pytest.raises(ValueError, match="at least 1"):
        rank_top_net_buyers(broker_activities, limit=limit)

    with pytest.raises(ValueError, match="at least 1"):
        rank_top_net_sellers(broker_activities, limit=limit)


def test_calculate_price_distance_pct():
    result = calculate_price_distance_pct(
        reference_price=1_000.0,
        close_price=1_050.0,
    )

    assert result == pytest.approx(5.0)


def test_calculate_price_distance_pct_returns_none_for_missing_values():
    assert (
        calculate_price_distance_pct(
            reference_price=None,
            close_price=1_050.0,
        )
        is None
    )
    assert (
        calculate_price_distance_pct(
            reference_price=1_000.0,
            close_price=None,
        )
        is None
    )


def test_calculate_price_distance_pct_rejects_non_positive_reference_price():
    with pytest.raises(ValueError, match="reference_price must be positive"):
        calculate_price_distance_pct(
            reference_price=0.0,
            close_price=1_050.0,
        )


def test_top_net_buyer_context_includes_cautionary_limitation(
    broker_activities,
):
    summary = summarize_top_net_buyer_context(
        broker_activities,
        close_price=7_000.0,
    )

    assert "SQ is the top net buyer" in summary
    assert "6,906.70" in summary
    assert "+1.35%" in summary
    assert "not confirmed support or resistance" in summary


def test_top_net_buyer_context_handles_no_net_buyer():
    summary = summarize_top_net_buyer_context(
        activities=(),
        close_price=1_000.0,
    )

    assert summary == (
        "No net-buying broker activity is available for the selected range."
    )


def test_broker_summary_metadata_preserves_request_scope():
    metadata = BrokerSummaryMetadata(
        ticker="BBCA",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 11),
        source="index_alpha",
        market="RG",
        investor="all",
    )

    assert metadata.ticker == "BBCA"
    assert metadata.start_date == date(2026, 9, 1)
    assert metadata.end_date == date(2026, 9, 11)
    assert metadata.source == "index_alpha"
    assert metadata.market == "RG"
    assert metadata.investor == "all"

def test_broker_summary_result_preserves_metadata_and_activities(
    broker_activities,
):
    metadata = BrokerSummaryMetadata(
        ticker="BBCA",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 11),
        source="mirae_csv",
        market="RG",
        investor="all",
    )
    result = BrokerSummaryResult(
        metadata=metadata,
        activities=broker_activities,
    )

    assert result.metadata.source == "mirae_csv"
    assert result.activities == broker_activities