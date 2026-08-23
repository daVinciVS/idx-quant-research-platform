import math

import pytest

from src.analytics.trade_plan import calculate_trade_plan


def test_trade_plan_calculates_pullback_and_breakout_levels():
    plan = calculate_trade_plan(
        close=1_000.0,
        atr14=100.0,
        resistance=1_120.0,
        six_month_high=1_250.0,
    )

    assert plan.pullback_entry_low == 950.0
    assert plan.pullback_entry_high == 1_000.0
    assert plan.pullback_stop_loss == 800.0
    assert plan.pullback_target_1 == 1_150.0
    assert plan.pullback_target_2 == 1_300.0
    assert plan.pullback_rrr == 1.5

    assert plan.breakout_entry == 1_120.0
    assert plan.breakout_stop_loss == 970.0
    assert plan.breakout_target_1 == 1_270.0
    assert plan.breakout_target_2 == 1_420.0
    assert plan.breakout_rrr == 2.0


def test_trade_plan_uses_resistance_when_it_exceeds_atr_target():
    plan = calculate_trade_plan(
        close=1_000.0,
        atr14=100.0,
        resistance=1_500.0,
        six_month_high=1_100.0,
    )

    assert plan.pullback_target_1 == 1_500.0
    assert plan.pullback_target_2 == 1_300.0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("close", 0.0),
        ("close", -1.0),
        ("atr14", 0.0),
        ("atr14", -10.0),
        ("resistance", 0.0),
        ("six_month_high", -1.0),
        ("close", math.nan),
        ("atr14", math.inf),
    ],
)
def test_trade_plan_rejects_invalid_numeric_inputs(field, value):
    valid_inputs = {
        "close": 1_000.0,
        "atr14": 100.0,
        "resistance": 1_120.0,
        "six_month_high": 1_250.0,
    }
    valid_inputs[field] = value

    with pytest.raises(ValueError, match="finite and greater than zero"):
        calculate_trade_plan(**valid_inputs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("close", "1000"),
        ("atr14", None),
        ("resistance", True),
        ("six_month_high", []),
    ],
)
def test_trade_plan_rejects_non_numeric_inputs(field, value):
    valid_inputs = {
        "close": 1_000.0,
        "atr14": 100.0,
        "resistance": 1_120.0,
        "six_month_high": 1_250.0,
    }
    valid_inputs[field] = value

    with pytest.raises(TypeError, match="must be a numeric value"):
        calculate_trade_plan(**valid_inputs)