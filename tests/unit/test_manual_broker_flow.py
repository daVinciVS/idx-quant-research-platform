from datetime import date
from pathlib import Path

from src.application.manual_broker_flow import (
    load_manual_broker_flow_context,
)

_FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_loader_returns_missing_file_message(tmp_path):
    result = load_manual_broker_flow_context(
        ticker="MDIA",
        start_date=date(2026, 9, 18),
        end_date=date(2026, 9, 19),
        region="all",
        latest_close=204.0,
        path=tmp_path / "missing.csv",
    )

    assert result.context is None
    assert result.message is not None
    assert "No local detailed Mirae broker-summary file" in result.message


def test_loader_returns_context_for_matching_manual_data():
    result = load_manual_broker_flow_context(
        ticker="MDIA",
        start_date=date(2026, 9, 18),
        end_date=date(2026, 9, 19),
        region="all",
        latest_close=204.0,
        path=_FIXTURES_DIR / "mirae_broker_summary_valid.csv",
    )

    assert result.message is None
    assert result.context is not None
    assert result.context.ticker == "MDIA"
    assert result.context.market == "ALL"
    assert result.context.top_net_buyer is not None
    assert result.context.top_net_buyer.broker_code == "YU"


def test_loader_returns_context_and_message_for_no_matching_rows():
    result = load_manual_broker_flow_context(
        ticker="BBCA",
        start_date=date(2026, 9, 18),
        end_date=date(2026, 9, 19),
        region="all",
        latest_close=9_000.0,
        path=_FIXTURES_DIR / "mirae_broker_summary_valid.csv",
    )

    assert result.context is not None
    assert result.context.top_net_buyer is None
    assert result.message is not None
    assert "No manual Mirae broker rows match" in result.message


def test_loader_returns_safe_message_for_invalid_manual_data():
    result = load_manual_broker_flow_context(
        ticker="MDIA",
        start_date=date(2026, 9, 18),
        end_date=date(2026, 9, 18),
        region="all",
        latest_close=204.0,
        path=_FIXTURES_DIR / "mirae_broker_summary_missing_column.csv",
    )

    assert result.context is None
    assert result.message is not None
    assert "Manual Mirae broker data could not be loaded" in result.message