from __future__ import annotations

from datetime import datetime
from typing import Protocol

import pandas as pd

from src.data.contracts import DataContractError, validate_ohlcv
from src.data.market_sessions import exclude_incomplete_daily_dataframe


class YahooFinanceError(RuntimeError):
    """Raised when Yahoo Finance daily OHLCV data cannot be loaded."""


class YahooDownloader(Protocol):
    """Minimal yfinance download contract used by the provider."""

    def download(
        self,
        tickers: str,
        *,
        period: str,
        interval: str,
        auto_adjust: bool,
        progress: bool,
        threads: bool,
    ) -> pd.DataFrame:
        """Return downloaded OHLCV data."""


def normalize_idx_ticker(ticker: str) -> str:
    """Normalize an IDX ticker to Yahoo Finance's .JK symbol format."""
    normalized = ticker.strip().upper()

    if normalized.endswith(".JK"):
        normalized = normalized[:-3]

    if not normalized:
        raise ValueError("Ticker must not be blank.")

    if not normalized.isalnum():
        raise ValueError(
            "Ticker must contain only letters and numbers before the .JK suffix."
        )

    return f"{normalized}.JK"


def load_yahoo_daily_ohlcv(
    ticker: str,
    *,
    as_of: datetime,
    period: str = "6mo",
    downloader: YahooDownloader | None = None,
) -> pd.DataFrame:
    """Load validated IDX daily OHLCV history from Yahoo Finance."""
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware.")

    normalized_ticker = normalize_idx_ticker(ticker)
    resolved_downloader = downloader or _default_downloader()

    try:
        raw_history = resolved_downloader.download(
            normalized_ticker,
            period=period,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except Exception as error:
        raise YahooFinanceError(
            f"Yahoo Finance request failed for {normalized_ticker}."
        ) from error

    if raw_history.empty:
        raise YahooFinanceError(
            f"Yahoo Finance returned no daily history for {normalized_ticker}."
        )

    try:
        normalized_history = _normalize_downloaded_history(raw_history)
        validated_history = validate_ohlcv(normalized_history)
    except DataContractError as error:
        raise YahooFinanceError(
            f"Yahoo Finance returned invalid daily history for {normalized_ticker}."
        ) from error

    complete_history = exclude_incomplete_daily_dataframe(
        validated_history,
        as_of=as_of,
    )

    if complete_history.empty:
        raise YahooFinanceError(
            f"No completed daily bars are available for {normalized_ticker}."
        )

    return complete_history


def _default_downloader() -> YahooDownloader:
    try:
        import yfinance as yf
    except ImportError as error:
        raise YahooFinanceError(
            "yfinance is required to load public market data."
        ) from error

    return yf


def _normalize_downloaded_history(
    raw_history: pd.DataFrame,
) -> pd.DataFrame:
    history = raw_history.copy()

    if isinstance(history.columns, pd.MultiIndex):
        history.columns = history.columns.get_level_values(0)

    history = history.reset_index()

    if "Date" not in history.columns and "index" in history.columns:
        history = history.rename(columns={"index": "Date"})


    required_columns = ("Date", "Open", "High", "Low", "Close", "Volume")
    missing_columns = [
        column
        for column in required_columns
        if column not in history.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise DataContractError(
            f"Yahoo Finance history is missing columns: {missing}."
        )

    return history.loc[:, required_columns]