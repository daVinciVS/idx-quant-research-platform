from __future__ import annotations

import streamlit as st

from src.application.broker_flow_context import BrokerFlowContext
from src.application.manual_broker_flow import (
    ManualBrokerFlowLoadResult,
    load_manual_broker_flow_context,
)


def render_manual_broker_flow_workspace() -> None:
    """Render a local-only workspace for manual Mirae broker entries."""
    st.subheader("Manual broker-flow workspace")
    st.caption(
        "Local-only analysis of manually entered Mirae broker-summary rows. "
        "This tab does not retrieve live data, connect to a broker, or use "
        "the public synthetic demo fixtures."
    )

    st.info(
        "To use this workspace, copy "
        "data/manual/mirae_broker_summary_manual.example.csv to "
        "data/manual/mirae_broker_summary_manual.csv and enter broker rows "
        "observed from the Mirae app. The local file is ignored by Git."
    )

    left_column, right_column = st.columns(2)

    with left_column:
        ticker = st.text_input(
            "Ticker",
            value="",
            placeholder="Example: MDIA",
            key="manual_broker_flow_ticker",
        )
        latest_close = st.number_input(
            "Latest close (Rp)",
            min_value=0.0,
            value=0.0,
            step=1.0,
            format="%.0f",
            key="manual_broker_flow_latest_close",
        )

    with right_column:
        selected_date = st.date_input(
            "Broker-summary date",
            key="manual_broker_flow_workspace_date",
        )
        region = st.selectbox(
            "Mirae region",
            options=("all", "foreign", "local"),
            format_func=lambda value: value.title(),
            key="manual_broker_flow_workspace_region",
        )

    should_load = st.button(
        "Load manual broker flow",
        type="primary",
        width="stretch",
        key="manual_broker_flow_workspace_load",
    )

    if not should_load:
        st.markdown(
            """
            <div class="callout">
                <strong>How to use this:</strong> Select one ticker and one
                broker-summary date in the Mirae app, choose the matching
                region, manually enter its paired buyer/seller rows in the
                local CSV file, then load the matching context here.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    normalized_ticker = ticker.strip().upper().replace(".JK", "")
    if not normalized_ticker:
        st.error("Enter an IDX ticker before loading broker flow.")
        return

    close_value = latest_close if latest_close > 0 else None
    result = load_manual_broker_flow_context(
        ticker=normalized_ticker,
        start_date=selected_date,
        end_date=selected_date,
        region=region,
        latest_close=close_value,
    )
    _render_load_result(result)


def _render_load_result(
    result: ManualBrokerFlowLoadResult,
) -> None:
    if result.message is not None:
        st.info(result.message)

    if result.context is None:
        return

    _render_context(result.context)


def _render_context(context: BrokerFlowContext) -> None:
    st.caption(
        f"Source: {context.source} | "
        f"Range: {context.start_date} to {context.end_date} | "
        f"Region: {context.investor.title()} | "
        f"Market: {_format_market_scope(context.market)}"
    )

    buyer_column, seller_column = st.columns(2)

    with buyer_column:
        st.markdown("#### Top net buyer")
        _render_reference(
            context.top_net_buyer,
            label="No net buyer is available.",
        )

    with seller_column:
        st.markdown("#### Top net seller")
        _render_reference(
            context.top_net_seller,
            label="No net seller is available.",
        )

    st.write(context.interpretation)
    st.caption(context.caveat)


def _render_reference(
    reference,
    *,
    label: str,
) -> None:
    if reference is None:
        st.write(label)
        return

    st.metric(
        reference.broker_code,
        _format_idr(reference.net_value),
    )
    st.write(
        f"Average price: {_format_price(reference.average_price)}"
    )
    st.write(
        "Distance to latest close: "
        f"{_format_percentage(reference.distance_to_close_pct)}"
    )

def _format_market_scope(value: str) -> str:
    if value == "ALL":
        return "All trade types"

    if value == "RG":
        return "Regular market"

    if value == "NG":
        return "Negotiated market"

    return value

def _format_idr(value: float) -> str:
    sign = "-" if value < 0 else ""
    absolute_value = abs(value)

    if absolute_value >= 1_000_000_000:
        return f"{sign}Rp{absolute_value / 1_000_000_000:,.2f}B"

    if absolute_value >= 1_000_000:
        return f"{sign}Rp{absolute_value / 1_000_000:,.2f}M"

    return f"{sign}Rp{absolute_value:,.0f}"


def _format_price(value: float | None) -> str:
    if value is None:
        return "Unavailable"

    return f"Rp{value:,.2f}"


def _format_percentage(value: float | None) -> str:
    if value is None:
        return "Unavailable"

    return f"{value:+.2f}%"