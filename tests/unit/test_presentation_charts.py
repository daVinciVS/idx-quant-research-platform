from src.analytics.trade_plan import calculate_trade_plan
from src.presentation.charts import build_trade_plan_levels


def test_trade_plan_levels_include_all_expected_rows():
    plan = calculate_trade_plan(
        close=1_000.0,
        atr14=50.0,
        resistance=1_100.0,
        six_month_high=1_200.0,
    )

    levels = build_trade_plan_levels(plan)

    assert list(levels.columns) == ["Level", "Price", "Category"]
    assert len(levels) == 9
    assert set(levels["Category"]) == {
        "Stop",
        "Entry zone",
        "Trigger",
        "Target",
    }
    assert levels.loc[
        levels["Level"] == "Pullback stop",
        "Price",
    ].item() == 900.0
    assert levels.loc[
        levels["Level"] == "Breakout trigger",
        "Price",
    ].item() == 1_100.0
    assert levels.loc[
        levels["Level"] == "Breakout target 2",
        "Price",
    ].item() == 1_250.0