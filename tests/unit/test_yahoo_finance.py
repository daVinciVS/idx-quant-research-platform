from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest
from src.data.yahoo_finance import (
    YahooFinanceError,
    _normalize_downloaded_history,
    load_yahoo_daily_ohlcv,
    normalize_idx_ticker,
)

_JAKARTA = ZoneInfo("Asia/Jakarta")


class FakeYahooDownloader:
    def __init__(
        self,
        history: pd.DataFrame | None = None,
        error: Exception | None = None,
    ) -> None:
        self.history = history
        self.error = error
        self.calls: list[dict[str, object]] = []

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
        self.calls.append(
            {
                "tickers": tickers,
                "period": period,
                "interval": interval,
                "auto_adjust": auto_adjust,
                "progress": progress,
                "threads": threads,
            }
        )

        if self.error is not None:
            raise self.error

        if self.history is None:
            return pd.DataFrame()

        return self.history.copy()


@pytest.fixture
def valid_history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [1_000.0, 1_010.0, 1_020.0],
            "High": [1_020.0, 1_030.0, 1_040.0],
            "Low": [990.0, 1_000.0, 1_010.0],
            "Close": [1_010.0, 1_020.0, 1_030.0],
            "Adj Close": [1_010.0, 1_020.0, 1_030.0],
            "Volume": [1_000_000, 1_100_000, 1_200_000],
        },
        index=pd.to_datetime(
            ["2026-09-16", "2026-09-17", "2026-09-18"]
        ),
    )

def test_normalizer_renames_anonymous_date_index(valid_history):
    normalized = _normalize_downloaded_history(valid_history)

    assert list(normalized.columns) == [
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]
    assert normalized["Date"].iloc[0] == pd.Timestamp("2026-09-16")


@pytest.mark.parametrize(
    ("ticker", "expected"),
    [
        ("BBCA", "BBCA.JK"),
        ("bbca", "BBCA.JK"),
        ("BBCA.JK", "BBCA.JK"),
        ("  mdia.jk  ", "MDIA.JK"),
    ],
)
def test_normalize_idx_ticker(ticker, expected):
    assert normalize_idx_ticker(ticker) == expected


@pytest.mark.parametrize("ticker", ["", "   ", "BBCA-JK", "BBCA.JK.JK"])
def test_normalize_idx_ticker_rejects_invalid_values(ticker):
    with pytest.raises(ValueError):
        normalize_idx_ticker(ticker)


def test_loader_normalizes_ticker_and_returns_valid_daily_history(
    valid_history,
):
    downloader = FakeYahooDownloader(history=valid_history)

    history = load_yahoo_daily_ohlcv(
        "bbca",
        as_of=datetime(2026, 9, 19, 12, tzinfo=_JAKARTA),
        downloader=downloader,
    )

    assert list(history.columns) == [
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]
    assert len(history) == 3
    assert history["Date"].is_monotonic_increasing
    assert downloader.calls == [
        {
            "tickers": "BBCA.JK",
            "period": "6mo",
            "interval": "1d",
            "auto_adjust": False,
            "progress": False,
            "threads": False,
        }
    ]


def test_loader_removes_incomplete_today_bar_while_jakarta_market_is_open(
    valid_history,
):
    today_history = valid_history.copy()
    today_history.loc[pd.Timestamp("2026-09-21")] = [
        1_030.0,
        1_050.0,
        1_020.0,
        1_040.0,
        1_040.0,
        1_300_000,
    ]
    downloader = FakeYahooDownloader(history=today_history)

    history = load_yahoo_daily_ohlcv(
        "BBCA",
        as_of=datetime(2026, 9, 21, 10, tzinfo=_JAKARTA),
        downloader=downloader,
    )

    assert len(history) == 3
    assert history["Date"].max() == pd.Timestamp("2026-09-18")


def test_loader_keeps_today_bar_after_jakarta_market_close(
    valid_history,
):
    today_history = valid_history.copy()
    today_history.loc[pd.Timestamp("2026-09-21")] = [
        1_030.0,
        1_050.0,
        1_020.0,
        1_040.0,
        1_040.0,
        1_300_000,
    ]
    downloader = FakeYahooDownloader(history=today_history)

    history = load_yahoo_daily_ohlcv(
        "BBCA",
        as_of=datetime(2026, 9, 21, 16, 1, tzinfo=_JAKARTA),
        downloader=downloader,
    )

    assert len(history) == 4
    assert history["Date"].max() == pd.Timestamp("2026-09-21")


def test_loader_rejects_empty_provider_history():
    with pytest.raises(
        YahooFinanceError,
        match="returned no daily history",
    ):
        load_yahoo_daily_ohlcv(
            "BBCA",
            as_of=datetime(2026, 9, 19, 12, tzinfo=_JAKARTA),
            downloader=FakeYahooDownloader(),
        )


def test_loader_wraps_provider_failure():
    with pytest.raises(
        YahooFinanceError,
        match="request failed for BBCA.JK",
    ):
        load_yahoo_daily_ohlcv(
            "BBCA",
            as_of=datetime(2026, 9, 19, 12, tzinfo=_JAKARTA),
            downloader=FakeYahooDownloader(
                error=ConnectionError("network unavailable")
            ),
        )


def test_loader_rejects_naive_as_of(valid_history):
    with pytest.raises(ValueError, match="timezone-aware"):
        load_yahoo_daily_ohlcv(
            "BBCA",
            as_of=datetime(2026, 9, 19, 12),
            downloader=FakeYahooDownloader(history=valid_history),
        )


def test_loader_wraps_invalid_history_contract():
    invalid_history = pd.DataFrame(
        {
            "Open": [1_000.0],
            "High": [1_010.0],
            "Low": [990.0],
            "Close": [1_005.0],
        },
        index=pd.to_datetime(["2026-09-18"]),
    )

    with pytest.raises(
        YahooFinanceError,
        match="returned invalid daily history",
    ):
        load_yahoo_daily_ohlcv(
            "BBCA",
            as_of=datetime(2026, 9, 19, 12, tzinfo=_JAKARTA),
            downloader=FakeYahooDownloader(history=invalid_history),
        )