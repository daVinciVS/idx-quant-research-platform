from __future__ import annotations

from pathlib import Path

import pandas as pd

_REQUIRED_COLUMNS = ("Date", "Open", "High", "Low", "Close", "Volume")
_DEMO_MARKET_DATA_DIR = (
    Path(__file__).resolve().parents[2] / "data" / "demo" / "market_data"
)
_CASE_FIXTURE_NAMES = {
    "consider_entry": "demo_entry_setup",
    "reduced_size": "demo_entry_setup",
}


def load_demo_ohlcv(case_id: str) -> pd.DataFrame:
    """Load validated public synthetic OHLCV data for one demo case."""
    normalized_case_id = case_id.strip().lower()
    path = _DEMO_MARKET_DATA_DIR / f"{normalized_case_id}.csv"

    if not path.exists():
        raise ValueError(
            f"No public market-data fixture exists for demo case: {case_id!r}."
        )

    frame = pd.read_csv(path, parse_dates=["Date"])
    _validate_demo_ohlcv(frame, case_id=normalized_case_id)

    return frame.copy()

def load_demo_case_ohlcv(case_id: str) -> pd.DataFrame | None:
    """Return public synthetic OHLCV data when a demo case has a fixture."""
    normalized_case_id = case_id.strip().lower()
    fixture_name = _CASE_FIXTURE_NAMES.get(normalized_case_id)

    if fixture_name is None:
        return None

    return load_demo_ohlcv(fixture_name)

def _validate_demo_ohlcv(
    frame: pd.DataFrame,
    *,
    case_id: str,
) -> None:
    missing_columns = [
        column
        for column in _REQUIRED_COLUMNS
        if column not in frame.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(
            f"Demo OHLCV fixture {case_id!r} is missing columns: {missing}."
        )

    if len(frame) < 80:
        raise ValueError(
            f"Demo OHLCV fixture {case_id!r} must contain at least 80 rows."
        )

    if frame["Date"].isna().any() or not frame["Date"].is_monotonic_increasing:
        raise ValueError(
            f"Demo OHLCV fixture {case_id!r} must have increasing valid dates."
        )

    numeric_columns = ["Open", "High", "Low", "Close", "Volume"]
    if frame[numeric_columns].isna().any().any():
        raise ValueError(
            f"Demo OHLCV fixture {case_id!r} contains missing numeric values."
        )

    if (frame[["Open", "High", "Low", "Close"]] <= 0).any().any():
        raise ValueError(
            f"Demo OHLCV fixture {case_id!r} must contain positive prices."
        )

    if (frame["Volume"] < 0).any():
        raise ValueError(
            f"Demo OHLCV fixture {case_id!r} must contain non-negative volume."
        )

    if (frame["High"] < frame[["Open", "Close", "Low"]].max(axis=1)).any():
        raise ValueError(
            f"Demo OHLCV fixture {case_id!r} has an invalid high price."
        )

    if (frame["Low"] > frame[["Open", "Close", "High"]].min(axis=1)).any():
        raise ValueError(
            f"Demo OHLCV fixture {case_id!r} has an invalid low price."
        )