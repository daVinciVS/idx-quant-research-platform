from src.analytics.decision import (
    DecisionInputs,
    DecisionLabel,
    evaluate_trade_decision,
)


def test_consider_entry_when_all_long_setup_gates_pass():
    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=True,
            trend_template_passed=True,
            relative_strength_positive=True,
            wyckoff_phase="Accumulation Phase D",
            extension_risk=False,
            risk_reward_ratio=2.5,
        )
    )

    assert decision.label == DecisionLabel.CONSIDER_ENTRY
    assert decision.confidence == "Medium"


def test_watchlist_when_setup_is_extended():
    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=True,
            trend_template_passed=True,
            relative_strength_positive=True,
            wyckoff_phase="Accumulation Phase D",
            extension_risk=True,
            risk_reward_ratio=2.5,
        )
    )

    assert decision.label == DecisionLabel.WATCHLIST
    assert "extended" in " ".join(decision.reasons).lower()


def test_avoid_when_trend_and_relative_strength_are_weak():
    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=True,
            trend_template_passed=False,
            relative_strength_positive=False,
            wyckoff_phase="Distribution Phase D",
            extension_risk=False,
            risk_reward_ratio=1.5,
        )
    )

    assert decision.label == DecisionLabel.AVOID


def test_insufficient_data_overrides_other_signals():
    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=False,
            trend_template_passed=True,
            relative_strength_positive=True,
            wyckoff_phase="Accumulation Phase D",
            extension_risk=False,
            risk_reward_ratio=3.0,
        )
    )

    assert decision.label == DecisionLabel.INSUFFICIENT_DATA


def test_abnormal_volatility_risk_returns_avoid():
    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=True,
            trend_template_passed=True,
            relative_strength_positive=True,
            wyckoff_phase="Accumulation Phase D",
            extension_risk=False,
            risk_reward_ratio=3.0,
            abnormal_volatility_risk=True,
        )
    )

    assert decision.label == DecisionLabel.AVOID