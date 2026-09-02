from __future__ import annotations


def format_currency_idr(value: float | None) -> str:
    """Format an optional numeric value as an integer Indonesian rupiah amount."""
    if value is None:
        return "N/A"
    return f"Rp {value:,.0f}"


def format_percent(value: float | None) -> str:
    """Format an optional decimal value as a percentage."""
    if value is None:
        return "N/A"
    return f"{value:.2%}"


def format_integer(value: int | None) -> str:
    """Format an optional integer for compact tabular display."""
    if value is None:
        return "N/A"
    return f"{value:,}"