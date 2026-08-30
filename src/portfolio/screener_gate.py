from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.analytics.decision import RiskCategory
from src.analytics.portfolio_risk import size_proposed_trade
from src.portfolio.ledger import load_open_positions, load_portfolio_config
from src.portfolio.models import OpenPosition, PortfolioConfig, ProposedTrade


@dataclass(frozen=True)
class PortfolioContext:
    config: PortfolioConfig
    positions: list[OpenPosition]


@dataclass(frozen=True)
class PortfolioGateResult:
    action: str
    plan_type: str
    recommended_quantity: int
    position_value: float | None
    initial_risk_amount: float | None
    initial_risk_pct: float | None
    projected_portfolio_heat_pct: float | None
    reasons: tuple[str, ...]


def load_portfolio_context(
    config_path: Path,
    positions_path: Path,
) -> PortfolioContext:
    """Load private portfolio files once for a read-only screening run."""
    config = load_portfolio_config(config_path)
    positions = load_open_positions(
        positions_path,
        lot_size=config.lot_size,
    )
    return PortfolioContext(config=config, positions=positions)


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    return number


def _risk_category_from_label(risk_label: str) -> RiskCategory:
    normalized = risk_label.strip().upper()

    if normalized == "SAFE (BLUECHIP / LIQUID)":
        return RiskCategory.SAFE
    if normalized == "MODERATE RISK (SECOND LINER)":
        return RiskCategory.MODERATE
    if normalized == "EXTREME RISK (SAHAM GORENGAN)":
        return RiskCategory.EXTREME

    return RiskCategory.UNKNOWN


def _not_applicable_result() -> PortfolioGateResult:
    return PortfolioGateResult(
        action="NOT APPLICABLE",
        plan_type="N/A",
        recommended_quantity=0,
        position_value=None,
        initial_risk_amount=None,
        initial_risk_pct=None,
        projected_portfolio_heat_pct=None,
        reasons=(
            "Portfolio sizing applies only to stock-level CONSIDER ENTRY candidates.",
        ),
    )


def _unavailable_result(reason: str) -> PortfolioGateResult:
    return PortfolioGateResult(
        action="UNAVAILABLE",
        plan_type="N/A",
        recommended_quantity=0,
        position_value=None,
        initial_risk_amount=None,
        initial_risk_pct=None,
        projected_portfolio_heat_pct=None,
        reasons=(reason,),
    )


def _review_required_result() -> PortfolioGateResult:
    return PortfolioGateResult(
        action="REVIEW REQUIRED",
        plan_type="N/A",
        recommended_quantity=0,
        position_value=None,
        initial_risk_amount=None,
        initial_risk_pct=None,
        projected_portfolio_heat_pct=None,
        reasons=(
            "No automatic order size was calculated because no pullback or "
            "breakout plan was selected.",
        ),
    )


def _invalid_plan_result(plan_type: str) -> PortfolioGateResult:
    return PortfolioGateResult(
        action="BLOCKED - INVALID TRADE PLAN",
        plan_type=plan_type,
        recommended_quantity=0,
        position_value=None,
        initial_risk_amount=None,
        initial_risk_pct=None,
        projected_portfolio_heat_pct=None,
        reasons=(
            "Selected trade-plan entry, stop, or target is unavailable or invalid.",
        ),
    )


def evaluate_portfolio_gate(
    row: dict[str, Any],
    context: PortfolioContext | None,
) -> PortfolioGateResult:
    """Return a read-only portfolio sizing recommendation for one screener row."""
    decision = str(row.get("Decision") or "").strip().upper()
    if decision != "CONSIDER ENTRY":
        return _not_applicable_result()

    if context is None:
        return _unavailable_result(
            "Portfolio config or positions ledger is unavailable."
        )

    screening_status = str(
        row.get("Screening Status") or ""
    ).strip().upper()

    if "PULLBACK" in screening_status:
        plan_type = "PULLBACK"
        entry_price = _finite_number(row.get("Pullback Entry Low"))
        stop_price = _finite_number(row.get("Pullback Stop Loss"))
        target_price = _finite_number(row.get("Pullback Target 1"))
    elif "BREAKOUT" in screening_status:
        plan_type = "BREAKOUT"
        entry_price = _finite_number(row.get("Breakout Trigger"))
        stop_price = _finite_number(row.get("Breakout Stop Loss"))
        target_price = _finite_number(row.get("Breakout Target 1"))
    else:
        return _review_required_result()

    if (
        entry_price is None
        or stop_price is None
        or target_price is None
        or entry_price <= 0
        or stop_price <= 0
        or target_price <= 0
        or stop_price >= entry_price
    ):
        return _invalid_plan_result(plan_type)

    proposed = ProposedTrade(
        ticker=str(row.get("Ticker") or "").strip().upper(),
        sector=None,
        entry_price=entry_price,
        stop_price=stop_price,
        target_price=target_price,
        risk_category=_risk_category_from_label(
            str(row.get("Risk Classification") or "")
        ),
    )

    result = size_proposed_trade(
        context.config,
        context.positions,
        proposed,
    )

    return PortfolioGateResult(
        action=result.action,
        plan_type=plan_type,
        recommended_quantity=result.quantity,
        position_value=result.position_value,
        initial_risk_amount=result.initial_risk_amount,
        initial_risk_pct=result.initial_risk_pct,
        projected_portfolio_heat_pct=result.projected_portfolio_heat_pct,
        reasons=result.reasons,
    )