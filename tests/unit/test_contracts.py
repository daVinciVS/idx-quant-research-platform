import pandas as pd
import pytest

from src.data.contracts import DataContractError, validate_ohlcv


def valid_ohlcv() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": ["2026-08-11", "2026-08-10"],
            "Open": [101.0, 100.0],
            "High": [103.0, 102.0],
            "Low": [100.0, 99.0],
            "Close": [102.0, 101.0],
            "Volume": [1_000, 900],
        }
    )


def test_validate_ohlcv_normalizes_dates_and_sorts_ascending():
    result = validate_ohlcv(valid_ohlcv())

    assert result["Date"].tolist() == [
        pd.Timestamp("2026-08-10"),
        pd.Timestamp("2026-08-11"),
    ]
    assert result["Close"].tolist() == [101.0, 102.0]


def test_validate_ohlcv_rejects_empty_history():
    with pytest.raises(DataContractError, match="must not be empty"):
        validate_ohlcv(pd.DataFrame())


def test_validate_ohlcv_rejects_missing_columns():
    history = valid_ohlcv().drop(columns=["Volume"])

    with pytest.raises(DataContractError, match="missing columns"):
        validate_ohlcv(history)


def test_validate_ohlcv_rejects_invalid_dates():
    history = valid_ohlcv()
    history.loc[0, "Date"] = "not-a-date"

    with pytest.raises(DataContractError, match="invalid dates"):
        validate_ohlcv(history)


def test_validate_ohlcv_rejects_duplicate_dates():
    history = valid_ohlcv()
    history.loc[1, "Date"] = history.loc[0, "Date"]

    with pytest.raises(DataContractError, match="duplicate dates"):
        validate_ohlcv(history)


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("Open", "not-numeric", "missing or non-numeric"),
        ("Volume", None, "missing or non-numeric"),
        ("Volume", -1, "negative volume"),
    ],
)
def test_validate_ohlcv_rejects_invalid_numeric_values(
    column,
    value,
    message,
):
    history = valid_ohlcv()

    if column == "Open" and isinstance(value, str):
        history[column] = history[column].astype("object")

    history.loc[0, column] = value

    with pytest.raises(DataContractError, match=message):
        validate_ohlcv(history)


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("High", 98.0, "High values below Low values"),
        ("High", 101.0, "High below Open or Close"),
        ("Low", 101.5, "Low above Open or Close"),
    ],
)
def test_validate_ohlcv_rejects_invalid_price_relationships(
    column,
    value,
    message,
):
    history = valid_ohlcv()
    history.loc[0, column] = value

    with pytest.raises(DataContractError, match=message):
        validate_ohlcv(history)


def test_validate_ohlcv_rejects_non_dataframe_input():
    with pytest.raises(TypeError, match="pandas DataFrame"):
        validate_ohlcv([])