from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from src.application.public_analysis import (
    PublicAnalysisError,
    PublicAnalysisResult,
    analyze_public_ticker,
)
from src.presentation.formatters import format_currency_idr
from src.presentation.market_chart import build_market_chart

_JAKARTA = ZoneInfo("Asia/Jakarta")


def render_public_ticker_dashboard() -> None:
    """Render public Yahoo daily-OHLCV ticker analysis."""
    st.markdown(
        '<div class="eyebrow">IDX EQUITY RESEARCH / PUBLIC DAILY DATA</div>',
        unsafe_allow_html=True,
    )
    st.title("Analyze an IDX ticker")
    st.markdown(
        '<div class="subtle-copy">Enter an IDX symbol such as BBCA, BBCA.JK, '
        "or TLKM. The analysis uses public daily OHLCV data only.</div>",
        unsafe_allow_html=True,
    )

    st.info(
        "Public daily-price technical analysis only. Broker summary, broker "
        "flow, foreign flow, and private data are not included. This is "
        "educational research support, not investment advice."
    )

    ticker = st.text_input(
        "IDX ticker",
        placeholder="BBCA",
        help="Enter the IDX code with or without the .JK suffix.",
    )
    analyze_clicked = st.button(
        "Analyze ticker",
        type="primary",
        use_container_width=False,
    )

    if not analyze_clicked:
        _render_empty_state()
        return

    if not ticker.strip():
        st.warning("Enter an IDX ticker before running public analysis.")
        return

    try:
        with st.spinner("Loading public daily OHLCV and calculating analysis..."):
            result = analyze_public_ticker(
                ticker,
                as_of=datetime.now(_JAKARTA),
            )
    except PublicAnalysisError:
        normalized_ticker = ticker.strip().upper()
        if not normalized_ticker.endswith(".JK"):
            normalized_ticker = f"{normalized_ticker}.JK"

        st.error(
            f"Public daily price data could not be loaded for {normalized_ticker}. "
            "Check the ticker and try again."
        )
        st.caption(
            "You can also explore the Public demo tab for deterministic "
            "illustrative scenarios."
        )
        return

    _render_public_result(result)


def _render_empty_state() -> None:
    st.caption(
        "Use the Public demo tab to explore deterministic scenarios without "
        "requesting live market data."
    )


def _render_public_result(result: PublicAnalysisResult) -> None:
    st.success(
        f"Loaded {result.ticker} daily OHLCV through {result.as_of_date}."
    )
    st.caption(result.data_status)

    metric_columns = st.columns(6)
    metric_columns[0].metric(
        "Latest close",
        format_currency_idr(result.latest_close),
    )
    metric_columns[1].metric("SMA 20", format_currency_idr(result.sma20))
    metric_columns[2].metric("SMA 50", format_currency_idr(result.sma50))
    metric_columns[3].metric("ATR 14", format_currency_idr(result.atr14))
    metric_columns[4].metric(
        "20D resistance",
        format_currency_idr(result.resistance_20d),
    )
    metric_columns[5].metric(
        "Six-month high",
        format_currency_idr(result.six_month_high),
    )

    st.divider()
    st.altair_chart(
        build_market_chart(
            result.history,
            ticker=result.ticker,
            trade_plan=result.trade_plan,
        ),
        use_container_width=True,
    )

    left_column, right_column = st.columns([1.3, 1.0], vertical_alignment="top")

    with left_column:
        st.subheader("Decision")
        st.metric("Current decision", result.decision.label.value)
        st.caption(f"Confidence: {result.decision.confidence}")

        st.markdown("**Why this result**")
        for reason in result.decision.reasons:
            st.write(f"- {reason}")

        st.markdown("**Next action**")
        st.write(result.decision.next_action)

    with right_column:
        st.subheader("Public-data limits")
        st.write(
            "- IHSG relative strength is not yet included in the public result."
        )
        st.write(
            "- Liquidity and risk classification are unavailable in this release."
        )
        st.write(
            "- Broker summary, broker flow, and foreign flow are intentionally "
            "excluded."
        )
        st.write(
            "- A conservative WAIT / NEUTRAL decision is expected while these "
            "inputs are unavailable."
        )

    if result.trade_plan is not None:
        st.divider()
        _render_trade_plan(result)
    else:
        st.info(
            "A trade plan is unavailable because the public daily history did "
            "not produce usable planning inputs."
        )


def _render_trade_plan(result: PublicAnalysisResult) -> None:
    plan = result.trade_plan
    if plan is None:
        return

    st.subheader("Rule-based trade plan")
    pullback_column, breakout_column = st.columns(2)

    with pullback_column:
        st.markdown("**Pullback scenario**")
        st.write(
            f"Preferred entry: {format_currency_idr(plan.pullback_entry_low)} "
            f"to {format_currency_idr(plan.pullback_entry_high)}"
        )
        st.write(f"Stop loss: {format_currency_idr(plan.pullback_stop_loss)}")
        st.write(f"Target 1: {format_currency_idr(plan.pullback_target_1)}")
        st.write(f"Target 2: {format_currency_idr(plan.pullback_target_2)}")
        st.write(f"Reward/risk: {plan.pullback_rrr:.2f}x")

    with breakout_column:
        st.markdown("**Breakout scenario**")
        st.write(f"Trigger: {format_currency_idr(plan.breakout_entry)}")
        st.write(f"Stop loss: {format_currency_idr(plan.breakout_stop_loss)}")
        st.write(f"Target 1: {format_currency_idr(plan.breakout_target_1)}")
        st.write(f"Target 2: {format_currency_idr(plan.breakout_target_2)}")
        st.write(f"Reward/risk: {plan.breakout_rrr:.2f}x")