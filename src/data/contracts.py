from __future__ import annotations

import pandas as pd

REQUIRED_OHLCV_COLUMNS = (
    "Date",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
)


class DataContractError(ValueError):
    """Raised when market data violates the OHLCV contract."""


def validate_ohlcv(
    history: pd.DataFrame,
    *,
    date_column: str = "Date",
) -> pd.DataFrame:
    """Return validated, ascending OHLCV data with normalized dates."""
    if not isinstance(history, pd.DataFrame):
        raise TypeError("history must be a pandas DataFrame")

    if history.empty:
        raise DataContractError("OHLCV history must not be empty")

    required_columns = (
        date_column,
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    )
    missing_columns = [
        column
        for column in required_columns
        if column not in history.columns
    ]

    if missing_columns:
        raise DataContractError(
            f"OHLCV history is missing columns: {missing_columns}"
        )

    validated = history.copy()
    validated[date_column] = pd.to_datetime(
        validated[date_column],
        errors="coerce",
        format="mixed",
    ).dt.normalize()

    if validated[date_column].isna().any():
        raise DataContractError("OHLCV history contains invalid dates")

    if validated[date_column].duplicated().any():
        raise DataContractError("OHLCV history contains duplicate dates")

    numeric_columns = ["Open", "High", "Low", "Close", "Volume"]

    for column in numeric_columns:
        validated[column] = pd.to_numeric(
            validated[column],
            errors="coerce",
        )

    if validated[numeric_columns].isna().any().any():
        raise DataContractError(
            "OHLCV history contains missing or non-numeric values"
        )

    if (validated["Volume"] < 0).any():
        raise DataContractError(
            "OHLCV history contains negative volume"
        )

    if (validated["High"] < validated["Low"]).any():
        raise DataContractError(
            "OHLCV history contains High values below Low values"
        )

    if (
        validated["High"]
        < validated[["Open", "Close"]].max(axis=1)
    ).any():
        raise DataContractError(
            "OHLCV history contains High below Open or Close"
        )

    if (
        validated["Low"]
        > validated[["Open", "Close"]].min(axis=1)
    ).any():
        raise DataContractError(
            "OHLCV history contains Low above Open or Close"
        )

    return validated.sort_values(date_column).reset_index(drop=True)