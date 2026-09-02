from __future__ import annotations

import streamlit as st

from src.analytics.decision import DecisionLabel
from src.application.paper_portfolio import (
    PaperPortfolioEvaluation,
    PaperPortfolioInputs,
    evaluate_paper_portfolio,
)
from src.application.public_demo import DemoCase
from src.presentation.charts import build_trade_plan_level_chart
from src.presentation.formatters import (
    format_currency_idr,
    format_integer,
    format_percent,
)

_DECISION_STYLES = {
    DecisionLabel.CONSIDER_ENTRY: ("status-positive", "CONSIDER ENTRY"),
    DecisionLabel.WATCHLIST: ("status-warning", "WATCHLIST"),
    DecisionLabel.WAIT: ("status-warning", "WAIT / NEUTRAL"),
    DecisionLabel.AVOID: ("status-negative", "AVOID"),
    DecisionLabel.INSUFFICIENT_DATA: ("status-info", "INSUFFICIENT DATA"),
}


def render_status_strip(case: DemoCase) -> None:
    """Render the compact decision and data-status summary."""
    style_name, label = _DECISION_STYLES[case.decision.label]

    st.markdown(
        f"""
        <div class="status-strip">
            <span class="status-badge {style_name}">{label}</span>
            <span class="status-meta">{case.ticker}</span>
            <span class="status-meta">Validated status: {case.data_status}</span>
            <span class="status-meta">As of: {case.as_of_date}</span>
            <span class="status-meta">Confidence: {case.decision.confidence}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_plain_english_takeaway(case: DemoCase) -> None:
    """Render a plain-language interpretation for nontechnical users."""
    st.markdown(
        f"""
        <div class="callout">
            <strong>Plain-English takeaway:</strong> {_plain_english_takeaway(case)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_level_map(case: DemoCase) -> None:
    """Render the illustrative deterministic trade-plan level chart."""
    st.subheader("Illustrative setup-level map")
    st.caption(
        "This visualizes deterministic entry, stop, and target levels from "
        "the demo trade plan. It is not historical price or candlestick data."
    )

    if case.trade_plan is None:
        st.info(
            "No setup levels are shown because this case has no eligible "
            "trade plan."
        )
        return

    st.altair_chart(
        build_trade_plan_level_chart(case.trade_plan),
        width="stretch",
    )


def render_decision_evidence(case: DemoCase) -> None:
    """Render rule evidence and the suggested next action."""
    st.subheader("Decision evidence")

    for reason in case.decision.reasons:
        st.markdown(f"- {reason}")

    st.markdown("### Suggested next action")
    st.write(case.decision.next_action)


def render_portfolio_gate(case: DemoCase) -> None:
    """Render the paper-portfolio sizing outcome and its rationale."""
    result = case.portfolio_result

    st.subheader("Portfolio gate")
    st.caption(
        "Illustrative paper portfolio: Rp 100,000,000 equity, "
        "Rp 50,000,000 available cash, 0.75% risk per trade, "
        "4.00% maximum portfolio heat."
    )

    action_class = _portfolio_action_class(result.action)
    first_reason = result.reasons[0] if result.reasons else "No rationale available."

    st.markdown(
        f"""
        <div class="panel">
            <span class="status-badge {action_class}">{result.action}</span>
            <div class="subtle-copy" style="margin-top: 0.75rem;">
                {first_reason}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left_column, right_column = st.columns(2)

    with left_column:
        _render_metric(
            "Plan type",
            result.plan_type,
            "Selected sizing scenario",
        )
        _render_metric(
            "Suggested quantity",
            format_integer(result.recommended_quantity),
            "Shares; rounded down to 100-share lots",
        )

    with right_column:
        _render_metric(
            "Position value",
            format_currency_idr(result.position_value),
            "Illustrative order notional",
        )
        _render_metric(
            "Initial risk / heat",
            format_currency_idr(result.initial_risk_amount),
            (
                f"{format_percent(result.initial_risk_pct)} initial risk | "
                f"{format_percent(result.projected_portfolio_heat_pct)} "
                "projected heat"
            ),
        )

    if len(result.reasons) > 1:
        st.markdown("### Gate rationale")
        for reason in result.reasons[1:]:
            st.markdown(f"- {reason}")

def render_paper_portfolio_sandbox(case: DemoCase) -> None:
    """Render an in-memory paper-portfolio sizing sandbox."""
    st.subheader("Paper portfolio sandbox")
    st.caption(
        "Change fictional assumptions to see how the existing portfolio-risk "
        "engine changes the sizing result. Nothing is saved."
    )

    if case.decision.label != DecisionLabel.CONSIDER_ENTRY:
        st.info(
            "This case cannot enter the paper-sizing sandbox because its "
            "stock-level decision is not CONSIDER ENTRY. Select Consider entry "
            "or Reduced size from the demo scenarios."
        )
        return

    if case.trade_plan is None:
        st.warning("This case does not include a valid trade plan to size.")
        return

    with st.form("paper_portfolio_sandbox"):
        left_column, right_column = st.columns(2)

        with left_column:
            equity = st.number_input(
                "Paper equity (Rp)",
                min_value=1_000_000.0,
                value=100_000_000.0,
                step=1_000_000.0,
                format="%.0f",
            )
            available_cash = st.number_input(
                "Available cash (Rp)",
                min_value=0.0,
                value=50_000_000.0,
                step=1_000_000.0,
                format="%.0f",
            )
            risk_per_trade_pct = st.number_input(
                "Risk per trade (%)",
                min_value=0.01,
                max_value=10.0,
                value=0.75,
                step=0.05,
                format="%.2f",
            )

        with right_column:
            max_risk_per_trade_pct = st.number_input(
                "Maximum risk per trade (%)",
                min_value=0.01,
                max_value=10.0,
                value=1.00,
                step=0.05,
                format="%.2f",
            )
            max_portfolio_heat_pct = st.number_input(
                "Maximum portfolio heat (%)",
                min_value=0.01,
                max_value=25.0,
                value=4.00,
                step=0.25,
                format="%.2f",
            )
            max_position_notional_pct = st.number_input(
                "Maximum position notional (%)",
                min_value=0.01,
                max_value=100.0,
                value=10.00,
                step=1.0,
                format="%.2f",
            )
            min_cash_reserve_pct = st.number_input(
                "Minimum cash reserve (%)",
                min_value=0.0,
                max_value=99.0,
                value=20.00,
                step=1.0,
                format="%.2f",
            )

        plan_type = st.radio(
            "Trade-plan scenario",
            options=("PULLBACK", "BREAKOUT"),
            horizontal=True,
        )
        submitted = st.form_submit_button(
            "Calculate paper position size",
            type="primary",
            width="stretch",
        )

    if not submitted:
        st.markdown(
            """
            <div class="callout">
                <strong>Try it:</strong> Start with the default assumptions,
                then reduce available cash or maximum position notional to see
                how the recommended quantity changes.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if available_cash > equity:
        st.error(
            "Available cash cannot exceed paper equity. Adjust the inputs and "
            "run the calculation again."
        )
        return

    if risk_per_trade_pct > max_risk_per_trade_pct:
        st.error(
            "Risk per trade cannot exceed the maximum risk per trade. Adjust "
            "the inputs and run the calculation again."
        )
        return

    inputs = PaperPortfolioInputs(
        equity=equity,
        available_cash=available_cash,
        risk_per_trade_pct=risk_per_trade_pct / 100,
        max_risk_per_trade_pct=max_risk_per_trade_pct / 100,
        max_portfolio_heat_pct=max_portfolio_heat_pct / 100,
        max_position_notional_pct=max_position_notional_pct / 100,
        min_cash_reserve_pct=min_cash_reserve_pct / 100,
        lot_size=100,
    )
    evaluation = evaluate_paper_portfolio(
        case=case,
        inputs=inputs,
        plan_type=plan_type,
    )

    _render_sandbox_evaluation(evaluation)

def _render_sandbox_evaluation(
    evaluation: PaperPortfolioEvaluation,
) -> None:
    if not evaluation.eligible or evaluation.result is None:
        st.warning(evaluation.message)
        return

    result = evaluation.result
    action_class = _portfolio_action_class(result.action)

    st.markdown(
        f"""
        <div class="panel">
            <span class="status-badge {action_class}">{result.action}</span>
            <div class="subtle-copy" style="margin-top: 0.75rem;">
                {evaluation.message}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left_column, right_column = st.columns(2)

    with left_column:
        _render_metric(
            "Selected plan",
            evaluation.plan_type,
            "Trade-plan scenario used for sizing",
        )
        _render_metric(
            "Suggested quantity",
            format_integer(result.quantity),
            "Shares; rounded down to IDX 100-share lots",
        )

    with right_column:
        _render_metric(
            "Position value",
            format_currency_idr(result.position_value),
            "Illustrative order notional",
        )
        _render_metric(
            "Initial risk / heat",
            format_currency_idr(result.initial_risk_amount),
            (
                f"{format_percent(result.initial_risk_pct)} initial risk | "
                f"{format_percent(result.projected_portfolio_heat_pct)} "
                "projected heat"
            ),
        )

    st.markdown("### Why this size")
    for reason in result.reasons:
        st.markdown(f"- {reason}")

def render_trade_plan_table(case: DemoCase) -> None:
    """Render a compact comparison of pullback and breakout scenarios."""
    st.subheader("Trade-plan scenarios")

    if case.trade_plan is None:
        st.info(
            "No trade plan is shown because this case did not pass the "
            "stock-level entry decision."
        )
        return

    plan = case.trade_plan
    comparison_rows = [
        {
            "Metric": "Entry",
            "Pullback plan": (
                f"Rp {plan.pullback_entry_low:,.0f} - "
                f"Rp {plan.pullback_entry_high:,.0f}"
            ),
            "Breakout plan": f"Rp {plan.breakout_entry:,.0f}",
        },
        {
            "Metric": "Protective stop",
            "Pullback plan": f"Rp {plan.pullback_stop_loss:,.0f}",
            "Breakout plan": f"Rp {plan.breakout_stop_loss:,.0f}",
        },
        {
            "Metric": "Target 1",
            "Pullback plan": f"Rp {plan.pullback_target_1:,.0f}",
            "Breakout plan": f"Rp {plan.breakout_target_1:,.0f}",
        },
        {
            "Metric": "Target 2",
            "Pullback plan": f"Rp {plan.pullback_target_2:,.0f}",
            "Breakout plan": f"Rp {plan.breakout_target_2:,.0f}",
        },
        {
            "Metric": "Risk / reward",
            "Pullback plan": f"{plan.pullback_rrr:.2f}x",
            "Breakout plan": f"{plan.breakout_rrr:.2f}x",
        },
    ]

    st.dataframe(
        comparison_rows,
        hide_index=True,
        width="stretch",
        column_config={
            "Metric": st.column_config.TextColumn("Metric", width="medium"),
            "Pullback plan": st.column_config.TextColumn(
                "Pullback plan",
                width="medium",
            ),
            "Breakout plan": st.column_config.TextColumn(
                "Breakout plan",
                width="medium",
            ),
        },
    )

    st.caption(
        "Pullback entries use an entry zone; breakout entries use a resistance "
        "trigger. Both are planning scenarios and require liquidity, spread, "
        "and execution review."
    )


def _plain_english_takeaway(case: DemoCase) -> str:
    if case.decision.label == DecisionLabel.CONSIDER_ENTRY:
        if case.portfolio_result.action == "ALLOWED - REDUCED SIZE":
            return (
                "The setup meets the stock-level entry rules, but the paper "
                "portfolio limits the order size to keep exposure controlled."
            )

        return (
            "The setup meets the current stock-level and paper-portfolio "
            "constraints, but execution still requires a liquidity and spread review."
        )

    if case.decision.label == DecisionLabel.WATCHLIST:
        return (
            "The setup has constructive evidence, but the current entry is "
            "not attractive enough to chase. Monitor it for a better location."
        )

    if case.decision.label == DecisionLabel.AVOID:
        return (
            "The system sees insufficient alignment between the trend and "
            "relative strength for a new long position."
        )

    if case.decision.label == DecisionLabel.INSUFFICIENT_DATA:
        return (
            "The system will not produce an entry recommendation until the "
            "daily market data is complete and validated."
        )

    return (
        "The current evidence is not aligned enough for an entry decision. "
        "Continue monitoring for clearer conditions."
    )


def _portfolio_action_class(action: str) -> str:
    if action.startswith("ALLOWED"):
        return "status-positive"
    if action.startswith("BLOCKED"):
        return "status-negative"
    if action == "REVIEW REQUIRED":
        return "status-warning"
    return "status-info"


def _render_metric(
    label: str,
    value: str,
    detail: str,
) -> None:
    st.markdown(
        f"""
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-detail">{detail}</div>
        <div style="height: 0.8rem"></div>
        """,
        unsafe_allow_html=True,
    )