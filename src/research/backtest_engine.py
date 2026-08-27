from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class TradeCostConfig:
    cost_bps_per_side: float = 20.0


@dataclass(frozen=True)
class SimulatedTrade:
    entry_price: float
    exit_price: float
    gross_return_pct: float
    net_return_pct: float


def simulate_trade(
    signal_score: int,
    entry_price: float,
    exit_price: float,
    cost_config: TradeCostConfig,
) -> SimulatedTrade | None:
    if signal_score < 1:
        return None

    gross_return_pct = ((exit_price / entry_price) - 1) * 100
    round_trip_cost_pct = (cost_config.cost_bps_per_side * 2) / 100
    net_return_pct = gross_return_pct - round_trip_cost_pct

    return SimulatedTrade(
        entry_price=entry_price,
        exit_price=exit_price,
        gross_return_pct=gross_return_pct,
        net_return_pct=net_return_pct,
    )