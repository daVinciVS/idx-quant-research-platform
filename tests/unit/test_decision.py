from src.analytics.decision import (
    DecisionInputs,
    DecisionLabel,
    RiskCategory,
    evaluate_trade_decision,
)


def test_safe_stock_can_be_considered_for_entry():
    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=True,
            trend_template_passed=True,
            relative_strength_positive=True,
            wyckoff_phase="Accumulation Phase D",
            extension_risk=False,
            risk_reward_ratio=2.5,
            risk_category=RiskCategory.SAFE,
        )
    )

    assert decision.label == DecisionLabel.CONSIDER_ENTRY
    assert decision.confidence == "Medium"


def test_moderate_risk_stock_is_downgraded_to_watchlist():
    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=True,
            trend_template_passed=True,
            relative_strength_positive=True,
            wyckoff_phase="Markup Phase",
            extension_risk=False,
            risk_reward_ratio=2.5,
            risk_category=RiskCategory.MODERATE,
        )
    )

    assert decision.label == DecisionLabel.WATCHLIST
    assert "moderate-risk" in " ".join(
        decision.reasons
    ).lower()


def test_extreme_risk_stock_is_avoided():
    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=True,
            trend_template_passed=True,
            relative_strength_positive=True,
            wyckoff_phase="Markup Phase",
            extension_risk=False,
            risk_reward_ratio=3.0,
            risk_category=RiskCategory.EXTREME,
        )
    )

    assert decision.label == DecisionLabel.AVOID


def test_unknown_risk_stock_cannot_be_considered_for_entry():
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

    assert decision.label == DecisionLabel.WAIT


def test_watchlist_when_setup_is_extended():
    decision = evaluate_trade_decision(
        DecisionInputs(
            has_sufficient_data=True,
            trend_template_passed=True,
            relative_strength_positive=True,
            wyckoff_phase="Accumulation Phase D",
            extension_risk=True,
            risk_reward_ratio=2.5,
            risk_category=RiskCategory.SAFE,
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
            risk_category=RiskCategory.SAFE,
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
            risk_category=RiskCategory.SAFE,
        )
    )

    assert decision.label == DecisionLabel.INSUFFICIENT_DATA