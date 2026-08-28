from __future__ import annotations

from math import floor

from src.analytics.decision import RiskCategory
from src.portfolio.models import (
    OpenPosition,
    PortfolioConfig,
    PositionSizeResult,
    ProposedTrade,
)


def calculate_position_risk(position: OpenPosition) -> float:
    """Return initial long-position risk using entry price and protective stop."""
    if (
        position.entry_price <= 0
        or position.stop_price <= 0
        or position.quantity <= 0
        or position.stop_price >= position.entry_price
    ):
        return 0.0

    return (position.entry_price - position.stop_price) * position.quantity


def calculate_open_portfolio_heat(
    positions: list[OpenPosition],
    equity: float,
) -> float:
    """Return active initial-stop portfolio heat as a decimal percentage."""
    if equity <= 0:
        raise ValueError("equity must be positive")

    total_risk = sum(
        calculate_position_risk(position)
        for position in positions
        if position.status.upper() == "OPEN"
    )
    return total_risk / equity


def _round_down_to_lot(quantity: float, lot_size: int) -> int:
    if lot_size <= 0:
        raise ValueError("lot_size must be positive")

    return floor(quantity / lot_size) * lot_size


def size_proposed_trade(
    config: PortfolioConfig,
    positions: list[OpenPosition],
    proposed: ProposedTrade,
) -> PositionSizeResult:
    """Apply deterministic sizing and portfolio-risk constraints to a long trade."""
    reasons: list[str] = []

    if proposed.risk_category != RiskCategory.SAFE:
        return PositionSizeResult(
            action="BLOCKED — RISK CATEGORY",
            quantity=0,
            position_value=0.0,
            initial_risk_amount=0.0,
            initial_risk_pct=0.0,
            projected_portfolio_heat_pct=calculate_open_portfolio_heat(
                positions,
                config.equity,
            ),
            reasons=(
                "Only SAFE risk-category candidates may receive a portfolio order.",
            ),
        )

    if (
        config.equity <= 0
        or config.available_cash < 0
        or config.risk_per_trade_pct <= 0
        or config.max_risk_per_trade_pct <= 0
        or config.max_portfolio_heat_pct <= 0
        or config.max_position_notional_pct <= 0
        or not 0 <= config.min_cash_reserve_pct < 1
    ):
        raise ValueError("portfolio configuration contains invalid values")

    if proposed.entry_price <= 0 or proposed.stop_price <= 0:
        return PositionSizeResult(
            action="BLOCKED — INVALID TRADE",
            quantity=0,
            position_value=0.0,
            initial_risk_amount=0.0,
            initial_risk_pct=0.0,
            projected_portfolio_heat_pct=calculate_open_portfolio_heat(
                positions,
                config.equity,
            ),
            reasons=("Entry and stop prices must be positive.",),
        )

    if proposed.stop_price >= proposed.entry_price:
        return PositionSizeResult(
            action="BLOCKED — INVALID TRADE",
            quantity=0,
            position_value=0.0,
            initial_risk_amount=0.0,
            initial_risk_pct=0.0,
            projected_portfolio_heat_pct=calculate_open_portfolio_heat(
                positions,
                config.equity,
            ),
            reasons=("Protective stop must be below entry price for a long trade.",),
        )

    risk_per_share = proposed.entry_price - proposed.stop_price
    normal_risk_budget = config.equity * config.risk_per_trade_pct
    max_risk_budget = config.equity * config.max_risk_per_trade_pct
    risk_budget = min(normal_risk_budget, max_risk_budget)

    max_notional = config.equity * config.max_position_notional_pct
    minimum_cash_reserve = config.equity * config.min_cash_reserve_pct
    spendable_cash = max(config.available_cash - minimum_cash_reserve, 0.0)

    quantity_by_risk = risk_budget / risk_per_share
    quantity_by_notional = max_notional / proposed.entry_price
    quantity_by_cash = spendable_cash / proposed.entry_price

    current_heat = calculate_open_portfolio_heat(positions, config.equity)
    remaining_heat_amount = max(
        (config.max_portfolio_heat_pct - current_heat) * config.equity,
        0.0,
    )
    quantity_by_heat = remaining_heat_amount / risk_per_share

    unrounded_quantity = min(
        quantity_by_risk,
        quantity_by_notional,
        quantity_by_cash,
        quantity_by_heat,
    )
    quantity = _round_down_to_lot(unrounded_quantity, config.lot_size)

    if quantity < config.lot_size:
        if remaining_heat_amount <= 0:
            action = "BLOCKED — PORTFOLIO HEAT LIMIT"
            reason = "Existing open-position risk already reaches the heat limit."
        elif spendable_cash < proposed.entry_price * config.lot_size:
            action = "BLOCKED — INSUFFICIENT CASH"
            reason = "Available cash after the required reserve cannot fund one board lot."
        elif max_notional < proposed.entry_price * config.lot_size:
            action = "BLOCKED — MAX POSITION SIZE"
            reason = "Maximum position-notional limit cannot fund one board lot."
        else:
            action = "BLOCKED — INVALID TRADE"
            reason = "Risk budget cannot fund one board lot at the proposed stop distance."

        return PositionSizeResult(
            action=action,
            quantity=0,
            position_value=0.0,
            initial_risk_amount=0.0,
            initial_risk_pct=0.0,
            projected_portfolio_heat_pct=current_heat,
            reasons=(reason,),
        )

    position_value = quantity * proposed.entry_price
    initial_risk_amount = quantity * risk_per_share
    initial_risk_pct = initial_risk_amount / config.equity
    projected_heat = current_heat + initial_risk_pct

    limiting_quantities = {
        "risk budget": quantity_by_risk,
        "maximum position notional": quantity_by_notional,
        "available cash after reserve": quantity_by_cash,
        "portfolio heat": quantity_by_heat,
    }
    binding_constraint = min(
        limiting_quantities,
        key=limiting_quantities.get,
    )

    if quantity < _round_down_to_lot(quantity_by_risk, config.lot_size):
        action = "ALLOWED — REDUCED SIZE"
        reasons.append(f"Position size reduced by {binding_constraint} constraint.")
    else:
        action = "ALLOWED"
        reasons.append("Position fits risk, cash, notional, and heat limits.")

    reasons.append(
        f"Initial risk: {initial_risk_amount:,.0f} "
        f"({initial_risk_pct:.2%} of equity)."
    )
    reasons.append(
        f"Projected portfolio heat: {projected_heat:.2%}."
    )

    return PositionSizeResult(
        action=action,
        quantity=quantity,
        position_value=position_value,
        initial_risk_amount=initial_risk_amount,
        initial_risk_pct=initial_risk_pct,
        projected_portfolio_heat_pct=projected_heat,
        reasons=tuple(reasons),
    )