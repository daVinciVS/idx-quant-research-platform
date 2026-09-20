from src.presentation.broker_flow_components import (
    _format_idr,
    _format_market_scope,
    _format_percentage,
    _format_price,
)


def test_format_idr_uses_billions_for_large_values():
    assert _format_idr(120_000_000_000.0) == "Rp120.00B"
    assert _format_idr(-79_670_000_000.0) == "-Rp79.67B"


def test_format_idr_uses_millions_for_mid_sized_values():
    assert _format_idr(25_000_000.0) == "Rp25.00M"


def test_format_idr_uses_full_value_for_small_values():
    assert _format_idr(250_000.0) == "Rp250,000"


def test_format_price_handles_available_and_missing_values():
    assert _format_price(198.0) == "Rp198.00"
    assert _format_price(None) == "Unavailable"


def test_format_percentage_handles_available_and_missing_values():
    assert _format_percentage(3.030303) == "+3.03%"
    assert _format_percentage(-2.0) == "-2.00%"
    assert _format_percentage(None) == "Unavailable"

def test_format_market_scope_uses_clear_labels():
    assert _format_market_scope("ALL") == "All trade types"
    assert _format_market_scope("RG") == "Regular market"
    assert _format_market_scope("NG") == "Negotiated market"
    assert _format_market_scope("OTHER") == "OTHER"