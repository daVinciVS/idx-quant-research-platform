import json

import pytest
from src.portfolio.ledger import (
    load_open_positions,
    load_portfolio_config,
)


@pytest.fixture
def valid_config() -> dict[str, float | int]:
    return {
        "equity": 100_000_000,
        "available_cash": 50_000_000,
        "risk_per_trade_pct": 0.0075,
        "max_risk_per_trade_pct": 0.01,
        "max_portfolio_heat_pct": 0.04,
        "max_position_notional_pct": 0.10,
        "min_cash_reserve_pct": 0.20,
        "lot_size": 100,
    }


def write_json(path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_csv(path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_load_portfolio_config_returns_valid_config(tmp_path, valid_config):
    path = tmp_path / "portfolio_config.json"
    write_json(path, valid_config)

    config = load_portfolio_config(path)

    assert config.equity == 100_000_000
    assert config.available_cash == 50_000_000
    assert config.lot_size == 100


def test_load_portfolio_config_rejects_missing_file(tmp_path):
    path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError, match="Portfolio config not found"):
        load_portfolio_config(path)


def test_load_portfolio_config_rejects_invalid_json(tmp_path):
    path = tmp_path / "portfolio_config.json"
    path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ValueError, match="not valid JSON"):
        load_portfolio_config(path)


def test_load_portfolio_config_rejects_missing_key(tmp_path, valid_config):
    path = tmp_path / "portfolio_config.json"
    valid_config.pop("equity")
    write_json(path, valid_config)

    with pytest.raises(ValueError, match="missing required key"):
        load_portfolio_config(path)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("equity", 0),
        ("available_cash", -1),
        ("risk_per_trade_pct", 0),
        ("max_risk_per_trade_pct", 0),
        ("max_portfolio_heat_pct", 0),
        ("max_position_notional_pct", 0),
        ("min_cash_reserve_pct", 1),
        ("lot_size", 0),
    ],
)
def test_load_portfolio_config_rejects_invalid_values(
    tmp_path,
    valid_config,
    field_name,
    value,
):
    path = tmp_path / "portfolio_config.json"
    valid_config[field_name] = value
    write_json(path, valid_config)

    with pytest.raises(ValueError):
        load_portfolio_config(path)


def test_load_portfolio_config_rejects_normal_risk_above_maximum(
    tmp_path,
    valid_config,
):
    path = tmp_path / "portfolio_config.json"
    valid_config["risk_per_trade_pct"] = 0.02
    valid_config["max_risk_per_trade_pct"] = 0.01
    write_json(path, valid_config)

    with pytest.raises(ValueError, match="cannot exceed"):
        load_portfolio_config(path)


def test_load_open_positions_normalizes_values(tmp_path):
    path = tmp_path / "positions.csv"
    write_csv(
        path,
        (
            "ticker,sector,entry_price,stop_price,quantity,current_price,status\n"
            "bbca.jk, Financials ,9500,9100,500,9600,open\n"
            "antm.jk,,3100,2920,1000,,CLOSED\n"
        ),
    )

    positions = load_open_positions(path)

    assert len(positions) == 2
    assert positions[0].ticker == "BBCA.JK"
    assert positions[0].sector == "Financials"
    assert positions[0].status == "OPEN"
    assert positions[1].sector is None
    assert positions[1].current_price is None
    assert positions[1].status == "CLOSED"


def test_load_open_positions_rejects_missing_file(tmp_path):
    path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError, match="Positions ledger not found"):
        load_open_positions(path)


def test_load_open_positions_rejects_missing_columns(tmp_path):
    path = tmp_path / "positions.csv"
    write_csv(path, "ticker,entry_price\nBBCA.JK,9500\n")

    with pytest.raises(ValueError, match="missing required column"):
        load_open_positions(path)


def test_load_open_positions_rejects_stop_at_or_above_entry(tmp_path):
    path = tmp_path / "positions.csv"
    write_csv(
        path,
        (
            "ticker,sector,entry_price,stop_price,quantity,current_price,status\n"
            "BBCA.JK,Financials,9500,9500,500,9600,OPEN\n"
        ),
    )

    with pytest.raises(ValueError, match="stop_price must be below"):
        load_open_positions(path)


def test_load_open_positions_rejects_non_numeric_price(tmp_path):
    path = tmp_path / "positions.csv"
    write_csv(
        path,
        (
            "ticker,sector,entry_price,stop_price,quantity,current_price,status\n"
            "BBCA.JK,Financials,not-a-price,9100,500,9600,OPEN\n"
        ),
    )

    with pytest.raises(ValueError, match="entry_price must be a numeric"):
        load_open_positions(path)


def test_load_open_positions_rejects_non_integer_quantity(tmp_path):
    path = tmp_path / "positions.csv"
    write_csv(
        path,
        (
            "ticker,sector,entry_price,stop_price,quantity,current_price,status\n"
            "BBCA.JK,Financials,9500,9100,500.5,9600,OPEN\n"
        ),
    )

    with pytest.raises(ValueError, match="quantity must be a positive integer"):
        load_open_positions(path)


def test_load_open_positions_rejects_non_lot_quantity(tmp_path):
    path = tmp_path / "positions.csv"
    write_csv(
        path,
        (
            "ticker,sector,entry_price,stop_price,quantity,current_price,status\n"
            "BBCA.JK,Financials,9500,9100,550,9600,OPEN\n"
        ),
    )

    with pytest.raises(ValueError, match="multiple of lot_size"):
        load_open_positions(path)


def test_load_open_positions_rejects_blank_ticker(tmp_path):
    path = tmp_path / "positions.csv"
    write_csv(
        path,
        (
            "ticker,sector,entry_price,stop_price,quantity,current_price,status\n"
            ",Financials,9500,9100,500,9600,OPEN\n"
        ),
    )

    with pytest.raises(ValueError, match="ticker is required"):
        load_open_positions(path)