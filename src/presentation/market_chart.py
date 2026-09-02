from __future__ import annotations

import altair as alt
import pandas as pd

from src.analytics.trade_plan import TradePlan


def prepare_market_chart_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Return sorted OHLCV data with deterministic trend overlays."""
    chart_data = frame.copy()

    chart_data["SMA20"] = chart_data["Close"].rolling(
        window=20,
        min_periods=20,
    ).mean()
    chart_data["SMA50"] = chart_data["Close"].rolling(
        window=50,
        min_periods=50,
    ).mean()

    return chart_data.sort_values("Date").reset_index(drop=True)


def build_demo_market_chart(
    frame: pd.DataFrame,
    trade_plan: TradePlan,
) -> alt.LayerChart:
    """Build a synthetic OHLCV research chart with setup-level overlays."""
    chart_data = prepare_market_chart_data(frame)
    latest_date = chart_data["Date"].max()

    price_scale = alt.Scale(zero=False)
    price_axis = alt.Axis(
    labelColor="#A9B4C0",
    labelFontSize=11,
    titleColor="#A9B4C0",
    gridColor="#2A3645",
    domain=False,
    format=",.0f",
)
    x_encoding = alt.X(
        "Date:T",
        title=None,
        axis=alt.Axis(
            format="%b %Y",
            labelColor="#A9B4C0",
            labelFontSize=11,
            grid=False,
            title=None,
            domain=False,
            tickColor="#2A3645",
        ),
    )

    high_low = (
        alt.Chart(chart_data)
        .mark_rule(color="#6E7C8C", opacity=0.8)
        .encode(
            x=x_encoding,
            y=alt.Y(
                "Low:Q",
                title="Price (Rp)",
                scale=price_scale,
                axis=price_axis,
            ),
            y2="High:Q",
            tooltip=[
                alt.Tooltip("Date:T", title="Date", format="%d %b %Y"),
                alt.Tooltip("Open:Q", title="Open", format=",.0f"),
                alt.Tooltip("High:Q", title="High", format=",.0f"),
                alt.Tooltip("Low:Q", title="Low", format=",.0f"),
                alt.Tooltip("Close:Q", title="Close", format=",.0f"),
                alt.Tooltip("Volume:Q", title="Volume", format=",d"),
            ],
        )
    )

    bodies = (
        alt.Chart(chart_data)
        .mark_bar(size=4)
        .encode(
            x=x_encoding,
            y=alt.Y(
                "Open:Q",
                scale=price_scale,
                axis=None,
            ),
            y2="Close:Q",
            color=alt.condition(
                "datum.Close >= datum.Open",
                alt.value("#5DD39E"),
                alt.value("#F26B6B"),
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="Date", format="%d %b %Y"),
                alt.Tooltip("Open:Q", title="Open", format=",.0f"),
                alt.Tooltip("High:Q", title="High", format=",.0f"),
                alt.Tooltip("Low:Q", title="Low", format=",.0f"),
                alt.Tooltip("Close:Q", title="Close", format=",.0f"),
                alt.Tooltip("Volume:Q", title="Volume", format=","),
            ],
        )
    )

    sma20 = (
        alt.Chart(chart_data)
        .mark_line(color="#74C0FC", strokeWidth=2)
        .encode(
            x=x_encoding,
            y=alt.Y(
                "SMA20:Q",
                scale=price_scale,
                axis=None,
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="Date", format="%d %b %Y"),
                alt.Tooltip("SMA20:Q", title="SMA 20", format=",.1f"),
            ],
        )
    )

    sma50 = (
        alt.Chart(chart_data)
        .mark_line(color="#F6C85F", strokeWidth=2)
        .encode(
            x=x_encoding,
            y=alt.Y(
                "SMA50:Q",
                scale=price_scale,
                axis=None,
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="Date", format="%d %b %Y"),
                alt.Tooltip("SMA50:Q", title="SMA 50", format=",.1f"),
            ],
        )
    )

    levels = pd.DataFrame(
        [
            {
                "Label": "Pullback entry low",
                "Price": trade_plan.pullback_entry_low,
                "Color": "#5DD39E",
            },
            {
                "Label": "Pullback entry high",
                "Price": trade_plan.pullback_entry_high,
                "Color": "#5DD39E",
            },
            {
                "Label": "Pullback stop",
                "Price": trade_plan.pullback_stop_loss,
                "Color": "#F26B6B",
            },
            {
                "Label": "Breakout trigger",
                "Price": trade_plan.breakout_entry,
                "Color": "#74C0FC",
            },
            {
                "Label": "Breakout stop",
                "Price": trade_plan.breakout_stop_loss,
                "Color": "#F26B6B",
            },
            {
                "Label": "Pullback target 1",
                "Price": trade_plan.pullback_target_1,
                "Color": "#D6A2E8",
            },
            {
                "Label": "Breakout target 1",
                "Price": trade_plan.breakout_target_1,
                "Color": "#D6A2E8",
            },
        ]
    )

    level_rules = (
        alt.Chart(levels)
        .mark_rule(strokeDash=[5, 4], strokeWidth=1.3)
        .encode(
            y=alt.Y(
                "Price:Q",
                scale=price_scale,
                axis=None,
            ),
            color=alt.Color(
                "Color:N",
                scale=None,
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Label:N", title="Trade-plan level"),
                alt.Tooltip("Price:Q", title="Price", format=",d"),
            ],
        )
    )

    last_close = pd.DataFrame(
        [
            {
                "Date": latest_date,
                "Close": chart_data["Close"].iloc[-1],
            }
        ]
    )

    latest_marker = (
        alt.Chart(last_close)
        .mark_point(
            color="#E8EDF2",
            filled=True,
            opacity=1,
            size=65,
            stroke="#0B0F14",
            strokeWidth=1,
        )
        .encode(
            x=alt.X("Date:T"),
            y=alt.Y(
                "Close:Q",
                scale=price_scale,
                axis=None,
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="As of", format="%d %b %Y"),
                alt.Tooltip("Close:Q", title="Latest close", format=",d"),
            ],
        )
    )

    price_chart = (
        alt.layer(
            high_low,
            bodies,
            sma20,
            sma50,
            level_rules,
            latest_marker,
        )
        .properties(
            height=420,
            title=alt.TitleParams(
                "Synthetic OHLCV fixture with trade-plan overlays",
                anchor="start",
                color="#E8EDF2",
                fontSize=15,
                fontWeight=600,
            ),
        )
    )

    volume_chart = (
        alt.Chart(chart_data)
        .mark_bar(opacity=0.7)
        .encode(
            x=x_encoding,
            y=alt.Y(
                "Volume:Q",
                title="Volume",
                axis=alt.Axis(
                    labelColor="#A9B4C0",
                    labelFontSize=11,
                    titleColor="#A9B4C0",
                    gridColor="#2A3645",
                    domain=False,
                    format="~s",
                ),
            ),
            color=alt.condition(
                "datum.Close >= datum.Open",
                alt.value("#386E57"),
                alt.value("#733E45"),
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="Date", format="%d %b %Y"),
                alt.Tooltip("Volume:Q", title="Volume", format=","),
            ],
        )
        .properties(height=110)
    )

    return (
        alt.vconcat(
            price_chart,
            volume_chart,
            spacing=8,
        )
        .resolve_scale(x="shared")
        .configure_view(strokeOpacity=0)
        .configure_axis(labelFont="sans-serif", titleFont="sans-serif")
        .configure_title(font="sans-serif")
    )