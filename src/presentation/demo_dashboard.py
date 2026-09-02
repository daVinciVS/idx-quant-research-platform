from __future__ import annotations

import streamlit as st

from src.application.public_demo import available_demo_cases, load_demo_case
from src.presentation.components import (
    render_decision_evidence,
    render_level_map,
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


def render_demo_dashboard() -> None:
    """Render the public deterministic demo dashboard."""
    selected_case_id = _render_sidebar()
    case = load_demo_case(selected_case_id)

    st.markdown(
        '<div class="eyebrow">IDX EQUITY RESEARCH / PUBLIC DEMO</div>',
        unsafe_allow_html=True,
    )
    st.title("IDX Quant Research Platform")
    st.markdown(
        '<div class="subtle-copy">Explainable swing-trade research and '
        "portfolio-risk planning for Indonesian equities.</div>",
        unsafe_allow_html=True,
    )

    render_status_strip(case)
    render_plain_english_takeaway(case)

    left_column, right_column = st.columns((1.65, 1), gap="large")

    with left_column:
        render_level_map(case)
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


def _render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-title">IDX Quant / Research</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="sidebar-caption">Public deterministic demonstration. '
            "No live prices, personal portfolio data, broker connectivity, or "
            "order execution.</div>",
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
                • Deterministic decision gates<br>
                • Explainable trade-plan scenarios<br>
                • Portfolio-aware sizing<br>
                • IDX 100-share board-lot rules<br>
                • Read-only research workflow
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected_case_id