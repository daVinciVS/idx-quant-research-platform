from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.application.broker_flow_context import (
    BrokerFlowContext,
    build_broker_flow_context,
)
from src.data.mirae_broker_summary import (
    MiraeBrokerSummaryError,
    load_mirae_broker_summary,
)

_MANUAL_MIRAE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "manual"
    / "mirae_broker_summary_manual.csv"
)


@dataclass(frozen=True)
class ManualBrokerFlowLoadResult:
    """Outcome of an optional local manual Mirae broker-flow request."""

    context: BrokerFlowContext | None
    message: str | None


def load_manual_broker_flow_context(
    *,
    ticker: str,
    start_date: date,
    end_date: date,
    region: str,
    latest_close: float | None,
    path: Path = _MANUAL_MIRAE_PATH,
) -> ManualBrokerFlowLoadResult:
    """Load optional local Mirae broker flow without breaking analysis."""
    if not path.exists():
        return ManualBrokerFlowLoadResult(
            context=None,
            message=(
                "No local detailed Mirae broker-summary file was found. "
                "Copy data/manual/mirae_broker_summary_manual.example.csv "
                "to data/manual/mirae_broker_summary_manual.csv, then "
                "enter manually observed broker rows."
            ),
        )

    try:
        result = load_mirae_broker_summary(
            path,
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            region=region,
        )
    except (OSError, MiraeBrokerSummaryError) as error:
        return ManualBrokerFlowLoadResult(
            context=None,
            message=f"Manual Mirae broker data could not be loaded: {error}",
        )

    context = build_broker_flow_context(
        result,
        latest_close=latest_close,
    )

    if not result.activities:
        return ManualBrokerFlowLoadResult(
            context=context,
            message=(
                "No manual Mirae broker rows match the selected ticker, "
                "date range, and region."
            ),
        )

    return ManualBrokerFlowLoadResult(
        context=context,
        message=None,
    )