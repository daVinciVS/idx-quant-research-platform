from src.presentation.formatters import (
    format_currency_idr,
    format_integer,
    format_percent,
)


def test_format_currency_idr_formats_whole_rupiah():
    assert format_currency_idr(1_234_567.89) == "Rp 1,234,568"


def test_format_currency_idr_returns_na_for_missing_value():
    assert format_currency_idr(None) == "N/A"


def test_format_percent_formats_decimal_percentage():
    assert format_percent(0.00675) == "0.68%"


def test_format_percent_returns_na_for_missing_value():
    assert format_percent(None) == "N/A"


def test_format_integer_uses_grouping_separator():
    assert format_integer(9_500) == "9,500"


def test_format_integer_returns_na_for_missing_value():
    assert format_integer(None) == "N/A"