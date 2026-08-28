from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from src.portfolio.models import OpenPosition, PortfolioConfig

_REQUIRED_CONFIG_KEYS = (
    "equity",
    "available_cash",
    "risk_per_trade_pct",
    "max_risk_per_trade_pct",
    "max_portfolio_heat_pct",
    "max_position_notional_pct",
    "min_cash_reserve_pct",
    "lot_size",
)

_REQUIRED_POSITION_COLUMNS = (
    "ticker",
    "sector",
    "entry_price",
    "stop_price",
    "quantity",
    "current_price",
    "status",
)


def _require_finite_number(
    value: Any,
    field_name: str,
    *,
    allow_zero: bool = False,
) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a numeric value.")

    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a numeric value.") from exc

    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite.")

    if number < 0 or (number == 0 and not allow_zero):
        comparator = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{field_name} must be {comparator}.")

    return number


def _require_percentage(
    value: Any,
    field_name: str,
    *,
    allow_zero: bool = False,
    allow_one: bool = False,
) -> float:
    percentage = _require_finite_number(
        value,
        field_name,
        allow_zero=allow_zero,
    )

    if percentage > 1 or (percentage == 1 and not allow_one):
        bound = "at most 1" if allow_one else "less than 1"
        raise ValueError(f"{field_name} must be {bound}.")

    return percentage


def _require_positive_integer(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a positive integer.")

    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a positive integer.") from exc

    if not math.isfinite(number) or number <= 0 or not number.is_integer():
        raise ValueError(f"{field_name} must be a positive integer.")

    return int(number)


def load_portfolio_config(path: Path) -> PortfolioConfig:
    """Load and validate a local portfolio configuration JSON file."""
    try:
        with path.open(encoding="utf-8") as file:
            payload = json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Portfolio config not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Portfolio config is not valid JSON: {path}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Portfolio config must be a JSON object.")

    missing_keys = [
        key for key in _REQUIRED_CONFIG_KEYS if key not in payload
    ]
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise ValueError(f"Portfolio config missing required key(s): {missing}")

    config = PortfolioConfig(
        equity=_require_finite_number(payload["equity"], "equity"),
        available_cash=_require_finite_number(
            payload["available_cash"],
            "available_cash",
            allow_zero=True,
        ),
        risk_per_trade_pct=_require_percentage(
            payload["risk_per_trade_pct"],
            "risk_per_trade_pct",
        ),
        max_risk_per_trade_pct=_require_percentage(
            payload["max_risk_per_trade_pct"],
            "max_risk_per_trade_pct",
        ),
        max_portfolio_heat_pct=_require_percentage(
            payload["max_portfolio_heat_pct"],
            "max_portfolio_heat_pct",
        ),
        max_position_notional_pct=_require_percentage(
            payload["max_position_notional_pct"],
            "max_position_notional_pct",
        ),
        min_cash_reserve_pct=_require_percentage(
            payload["min_cash_reserve_pct"],
            "min_cash_reserve_pct",
            allow_zero=True,
        ),
        lot_size=_require_positive_integer(payload["lot_size"], "lot_size"),
    )

    if config.risk_per_trade_pct > config.max_risk_per_trade_pct:
        raise ValueError(
            "risk_per_trade_pct cannot exceed max_risk_per_trade_pct."
        )

    return config


def _optional_finite_number(
    value: str | None,
    field_name: str,
    row_number: int,
) -> float | None:
    if value is None or not value.strip():
        return None

    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: {field_name} must be a numeric value."
        ) from exc

    if not math.isfinite(number) or number <= 0:
        raise ValueError(
            f"Row {row_number}: {field_name} must be a positive finite number."
        )

    return number


def _required_positive_number(
    value: str | None,
    field_name: str,
    row_number: int,
) -> float:
    number = _optional_finite_number(value, field_name, row_number)
    if number is None:
        raise ValueError(
            f"Row {row_number}: {field_name} is required."
        )
    return number


def load_open_positions(path: Path, lot_size: int = 100) -> list[OpenPosition]:
    """Load and validate a local portfolio positions CSV ledger."""
    if lot_size <= 0:
        raise ValueError("lot_size must be positive.")

    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                raise ValueError("Positions ledger must include a header row.")

            fieldnames = {
                field.strip() for field in reader.fieldnames if field
            }
            missing_columns = [
                column
                for column in _REQUIRED_POSITION_COLUMNS
                if column not in fieldnames
            ]
            if missing_columns:
                missing = ", ".join(missing_columns)
                raise ValueError(
                    "Positions ledger missing required column(s): "
                    f"{missing}"
                )

            positions: list[OpenPosition] = []

            for row_number, row in enumerate(reader, start=2):
                ticker = (row.get("ticker") or "").strip().upper()
                if not ticker:
                    raise ValueError(f"Row {row_number}: ticker is required.")

                sector_value = (row.get("sector") or "").strip()
                sector = sector_value or None

                entry_price = _required_positive_number(
                    row.get("entry_price"),
                    "entry_price",
                    row_number,
                )
                stop_price = _required_positive_number(
                    row.get("stop_price"),
                    "stop_price",
                    row_number,
                )

                quantity = _require_positive_integer(
                    row.get("quantity"),
                    f"Row {row_number}: quantity",
                )
                if quantity % lot_size != 0:
                    raise ValueError(
                        f"Row {row_number}: quantity must be a multiple "
                        f"of lot_size ({lot_size})."
                    )

                current_price = _optional_finite_number(
                    row.get("current_price"),
                    "current_price",
                    row_number,
                )

                status = (row.get("status") or "").strip().upper()
                if not status:
                    raise ValueError(f"Row {row_number}: status is required.")

                if status == "OPEN" and stop_price >= entry_price:
                    raise ValueError(
                        f"Row {row_number}: stop_price must be below "
                        "entry_price for an OPEN long position."
                    )

                positions.append(
                    OpenPosition(
                        ticker=ticker,
                        sector=sector,
                        entry_price=entry_price,
                        stop_price=stop_price,
                        quantity=quantity,
                        current_price=current_price,
                        status=status,
                    )
                )
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Positions ledger not found: {path}") from exc

    return positions