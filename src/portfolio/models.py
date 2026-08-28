from __future__ import annotations

from dataclasses import dataclass

from src.analytics.decision import RiskCategory


@dataclass(frozen=True)
class PortfolioConfig:
    equity: float
    available_cash: float
    risk_per_trade_pct: float
    max_risk_per_trade_pct: float
    max_portfolio_heat_pct: float
    max_position_notional_pct: float
    min_cash_reserve_pct: float
    lot_size: int = 100


@dataclass(frozen=True)
class OpenPosition:
    ticker: str
    sector: str | None
    entry_price: float
    stop_price: float
    quantity: int
    current_price: float | None
    status: str


@dataclass(frozen=True)
class ProposedTrade:
    ticker: str
    sector: str | None
    entry_price: float
    stop_price: float
    target_price: float | None
    risk_category: RiskCategory


@dataclass(frozen=True)
class PositionSizeResult:
    action: str
    quantity: int
    position_value: float
    initial_risk_amount: float
    initial_risk_pct: float
    projected_portfolio_heat_pct: float
    reasons: tuple[str, ...]