from __future__ import annotations

import streamlit as st

from src.application.public_demo import (
    DemoCase,
    available_demo_cases,
    load_demo_case,
)
from src.presentation.components import (
    render_decision_evidence,
    render_market_context_chart,
    render_paper_portfolio_sandbox,
    render_plain_english_takeaway,
    render_portfolio_gate,
    render_status_strip,
    render_trade_plan_table,
)

_CASE_LABELS = {
    "avoid": "Avoid - weak trend and relative strength",
    "watchlist": "Watchlist - extended entry risk",
    "consider_entry": "Consider entry - aligned setup",
    "reduced_size": "Reduced size - portfolio constraint",
    "insufficient_data": "Insufficient data - safety override",
}

_DEMO_CASE_STATE_KEY = "public_demo_case_id"


def render_demo_sidebar() -> DemoCase:
    """Render the public demo selector and return its selected case."""
    _initialize_demo_case_state()

    with st.sidebar:
        st.markdown(
            '<div class="sidebar-title">Demo scenario selector</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="sidebar-caption">Choose the deterministic case used by the '
            "Public demo and Paper portfolio sandbox tabs. It does not affect live "
            "ticker analysis.</div>",
            unsafe_allow_html=True,
        )
        st.divider()

        st.markdown(
            '<div class="sidebar-title">Demo scenarios</div>',
            unsafe_allow_html=True,
        )
        selected_case_id = st.selectbox(
            "Select a case",
            options=available_demo_cases(),
            format_func=lambda case_id: _CASE_LABELS[case_id],
            key=_DEMO_CASE_STATE_KEY,
            label_visibility="collapsed",
        )

        st.divider()
        st.markdown(
            '<div class="sidebar-title">System scope</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="sidebar-caption">
                - Deterministic decision gates<br>
                - Explainable trade-plan scenarios<br>
                - Portfolio-aware sizing<br>
                - IDX 100-share board-lot rules<br>
                - Read-only research workflow
            </div>
            """,
            unsafe_allow_html=True,
        )

    return load_demo_case(selected_case_id)


def render_demo_research(case: DemoCase) -> None:
    """Render deterministic demo research for the selected public case."""
    st.markdown(
        '<div class="eyebrow">IDX EQUITY RESEARCH / PUBLIC DEMO</div>',
        unsafe_allow_html=True,
    )
    st.title("Public demo")
    st.markdown(
        '<div class="subtle-copy">Explore deterministic examples of explainable '
        "swing-trade research and risk-aware decision gates.</div>",
        unsafe_allow_html=True,
    )

    render_status_strip(case)
    render_plain_english_takeaway(case)

    left_column, spacer_column, right_column = st.columns(
        [3.4, 0.25, 1.25],
        vertical_alignment="top",
    )

    with left_column:
        render_market_context_chart(case)
        st.divider()
        render_decision_evidence(case)
        st.divider()
        render_trade_plan_table(case)

    with right_column:
        render_portfolio_gate(case)

    st.markdown(
        """
        <div class="footer-note">
            <strong>Research and education only.</strong> This demonstration uses
            fictional tickers and deterministic inputs. It does not retrieve live
            prices, provide investment advice, store personal data, execute trades,
            or modify a portfolio ledger. Historical and illustrative outputs do
            not guarantee future performance.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_demo_sandbox(case: DemoCase) -> None:
    """Render paper-portfolio sandbox for the selected public demo case."""
    st.markdown(
        '<div class="eyebrow">IDX EQUITY RESEARCH / PORTFOLIO SANDBOX</div>',
        unsafe_allow_html=True,
    )
    st.title("Paper portfolio sandbox")
    st.markdown(
        '<div class="subtle-copy">Explore position-size and portfolio-risk '
        "constraints using the selected deterministic demo scenario.</div>",
        unsafe_allow_html=True,
    )

    render_paper_portfolio_sandbox(case)

    st.markdown(
        """
        <div class="footer-note">
            <strong>Research and education only.</strong> This sandbox is
            in-memory and illustrative. It does not retrieve live prices, store
            a portfolio, execute trades, or provide investment advice.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _initialize_demo_case_state() -> None:
    if _DEMO_CASE_STATE_KEY not in st.session_state:
        st.session_state[_DEMO_CASE_STATE_KEY] = available_demo_cases()[0]