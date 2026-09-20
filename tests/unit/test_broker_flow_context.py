from datetime import date

import pytest
from src.application.broker_flow_context import (
    build_broker_flow_context,
)
from src.domain.broker_summary import (
    BrokerActivity,
    BrokerSummaryMetadata,
    BrokerSummaryResult,
)


@pytest.fixture
def broker_summary_result() -> BrokerSummaryResult:
    metadata = BrokerSummaryMetadata(
        ticker="MDIA",
        start_date=date(2026, 9, 18),
        end_date=date(2026, 9, 19),
        source="mirae_manual",
        market="RG",
        investor="all",
    )
    activities = (
        BrokerActivity(
            broker_code="YU",
            buy_frequency=0,
            buy_volume=0,
            buy_value=120_000_000_000.0,
            sell_frequency=0,
            sell_volume=0,
            sell_value=0.0,
            buy_average_price=198.0,
            sell_average_price=None,
        ),
        BrokerActivity(
            broker_code="SS",
            buy_frequency=0,
            buy_volume=0,
            buy_value=0.0,
            sell_frequency=0,
            sell_volume=0,
            sell_value=79_670_000_000.0,
            buy_average_price=None,
            sell_average_price=200.0,
        ),
        BrokerActivity(
            broker_code="CC",
            buy_frequency=0,
            buy_volume=0,
            buy_value=0.0,
            sell_frequency=0,
            sell_volume=0,
            sell_value=36_750_000_000.0,
            buy_average_price=None,
            sell_average_price=199.0,
        ),
    )

    return BrokerSummaryResult(
        metadata=metadata,
        activities=activities,
    )


def test_context_contains_source_scope_and_top_references(
    broker_summary_result,
):
    context = build_broker_flow_context(
        broker_summary_result,
        latest_close=204.0,
    )

    assert context.ticker == "MDIA"
    assert context.source == "mirae_manual"
    assert context.start_date == "2026-09-18"
    assert context.end_date == "2026-09-19"
    assert context.market == "RG"
    assert context.investor == "all"
    assert context.latest_close == 204.0

    assert context.top_net_buyer is not None
    assert context.top_net_buyer.broker_code == "YU"
    assert context.top_net_buyer.net_value == 120_000_000_000.0
    assert context.top_net_buyer.average_price == 198.0
    assert context.top_net_buyer.distance_to_close_pct == pytest.approx(
        3.030303,
    )

    assert context.top_net_seller is not None
    assert context.top_net_seller.broker_code == "SS"
    assert context.top_net_seller.net_value == -79_670_000_000.0
    assert context.top_net_seller.average_price == 200.0
    assert context.top_net_seller.distance_to_close_pct == pytest.approx(
        2.0,
    )


def test_context_interpretation_names_top_buyer_and_seller(
    broker_summary_result,
):
    context = build_broker_flow_context(
        broker_summary_result,
        latest_close=204.0,
    )

    assert context.interpretation == (
        "YU is the top net buyer and SS is the top net seller over the "
        "selected range."
    )
    assert "does not identify beneficial owners" in context.caveat


def test_context_handles_empty_broker_summary():
    result = BrokerSummaryResult(
        metadata=BrokerSummaryMetadata(
            ticker="MDIA",
            start_date=date(2026, 9, 18),
            end_date=date(2026, 9, 18),
            source="mirae_manual",
            market="RG",
            investor="foreign",
        ),
        activities=(),
    )

    context = build_broker_flow_context(
        result,
        latest_close=204.0,
    )

    assert context.top_net_buyer is None
    assert context.top_net_seller is None
    assert context.interpretation == (
        "No net buyer or net seller is available for the selected "
        "broker-summary range."
    )


def test_context_handles_missing_latest_close(broker_summary_result):
    context = build_broker_flow_context(
        broker_summary_result,
        latest_close=None,
    )

    assert context.latest_close is None
    assert context.top_net_buyer is not None
    assert context.top_net_buyer.distance_to_close_pct is None
    assert context.top_net_seller is not None
    assert context.top_net_seller.distance_to_close_pct is None


@pytest.mark.parametrize("latest_close", [0.0, -1.0])
def test_context_rejects_non_positive_latest_close(
    broker_summary_result,
    latest_close,
):
    with pytest.raises(
        ValueError,
        match="latest_close must be positive",
    ):
        build_broker_flow_context(
            broker_summary_result,
            latest_close=latest_close,
        )