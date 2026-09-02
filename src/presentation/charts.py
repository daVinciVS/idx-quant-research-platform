from __future__ import annotations

import altair as alt
import pandas as pd

from src.analytics.trade_plan import TradePlan

_LEVEL_CATEGORY_COLORS = {
    "Stop": "#F26B6B",
    "Entry zone": "#5DD39E",
    "Trigger": "#74C0FC",
    "Target": "#D6A2E8",
}


def build_trade_plan_levels(trade_plan: TradePlan) -> pd.DataFrame:
    """Return plot-ready levels for an illustrative demo trade-plan map."""
    return pd.DataFrame(
        [
            {
                "Level": "Pullback stop",
                "Price": trade_plan.pullback_stop_loss,
                "Category": "Stop",
            },
            {
                "Level": "Pullback entry low",
                "Price": trade_plan.pullback_entry_low,
                "Category": "Entry zone",
            },
            {
                "Level": "Pullback entry high",
                "Price": trade_plan.pullback_entry_high,
                "Category": "Entry zone",
            },
            {
                "Level": "Breakout stop",
                "Price": trade_plan.breakout_stop_loss,
                "Category": "Stop",
            },
            {
                "Level": "Breakout trigger",
                "Price": trade_plan.breakout_entry,
                "Category": "Trigger",
            },
            {
                "Level": "Pullback target 1",
                "Price": trade_plan.pullback_target_1,
                "Category": "Target",
            },
            {
                "Level": "Breakout target 1",
                "Price": trade_plan.breakout_target_1,
                "Category": "Target",
            },
            {
                "Level": "Pullback target 2",
                "Price": trade_plan.pullback_target_2,
                "Category": "Target",
            },
            {
                "Level": "Breakout target 2",
                "Price": trade_plan.breakout_target_2,
                "Category": "Target",
            },
        ]
    )


def build_trade_plan_level_chart(trade_plan: TradePlan) -> alt.Chart:
    """Build a responsive Altair bar chart for deterministic setup levels."""
    levels = build_trade_plan_levels(trade_plan)
    category_scale = alt.Scale(
        domain=list(_LEVEL_CATEGORY_COLORS),
        range=list(_LEVEL_CATEGORY_COLORS.values()),
    )

    return (
        alt.Chart(levels)
        .mark_bar(cornerRadiusEnd=3, height=20)
        .encode(
            y=alt.Y(
                "Level:N",
                sort=alt.SortField("Price", order="descending"),
                title=None,
                axis=alt.Axis(
                    labelColor="#A9B4C0",
                    labelFontSize=12,
                    labelLimit=180,
                    ticks=False,
                    domain=False,
                ),
            ),
            x=alt.X(
                "Price:Q",
                title="Price level (Rp)",
                axis=alt.Axis(
                    labelColor="#A9B4C0",
                    titleColor="#A9B4C0",
                    gridColor="#2A3645",
                    domain=False,
                    format=",.0f",
                ),
            ),
            color=alt.Color(
                "Category:N",
                scale=category_scale,
                legend=alt.Legend(
                    title=None,
                    labelColor="#A9B4C0",
                    labelFontSize=12,
                    orient="bottom",
                ),
            ),
            tooltip=[
                alt.Tooltip("Level:N", title="Level"),
                alt.Tooltip("Category:N", title="Type"),
                alt.Tooltip("Price:Q", title="Price", format=","),
            ],
        )
        .properties(height=300)
        .configure_view(strokeOpacity=0)
        .configure_axis(labelFont="sans-serif", titleFont="sans-serif")
        .configure_legend(labelFont="sans-serif")
    )