import pytest
from generate_report import AnalyticsEngine


def build_validation(
    *,
    strategy_return: float = -11.6,
    benchmark_return: float = 4.25,
    num_trades: int = 17,
) -> dict[str, object]:
    return {
        "ticker": "BBCA",
        "test_observations": 250,
        "num_trades": num_trades,
        "holding_period_days": 5,
        "cost_bps_per_side": 20.0,
        "round_trip_cost_pct": 0.4,
        "strategy": {
            "cumulative_return_pct": strategy_return,
            "sharpe_ratio": -4.35,
            "max_drawdown_pct": -13.37,
        },
        "benchmark_IHSG": {
            "cumulative_return_pct": benchmark_return,
        },
    }


def test_build_backtest_validation_summary_returns_expected_metrics():
    engine = AnalyticsEngine()

    summary = engine.build_backtest_validation_summary(
        build_validation()
    )

    assert summary["test_observations"] == 250
    assert summary["num_trades"] == 17
    assert summary["holding_period_days"] == 5
    assert summary["round_trip_cost_pct"] == pytest.approx(0.4)
    assert summary["strategy_return_pct"] == pytest.approx(-11.6)
    assert summary["benchmark_return_pct"] == pytest.approx(4.25)
    assert summary["excess_return_pct"] == pytest.approx(-15.85)
    assert summary["strategy_sharpe_ratio"] == pytest.approx(-4.35)
    assert summary["strategy_max_drawdown_pct"] == pytest.approx(-13.37)


def test_summary_warns_for_small_sample_and_underperformance():
    engine = AnalyticsEngine()

    summary = engine.build_backtest_validation_summary(
        build_validation(
            strategy_return=-11.6,
            benchmark_return=4.25,
            num_trades=17,
        )
    )

    assert summary["warnings"] == [
        "Small sample: fewer than 20 completed trades.",
        "Strategy underperformed the matched IHSG benchmark.",
    ]


def test_summary_has_no_warnings_for_large_sample_outperformance():
    engine = AnalyticsEngine()

    summary = engine.build_backtest_validation_summary(
        build_validation(
            strategy_return=20.0,
            benchmark_return=4.25,
            num_trades=30,
        )
    )

    assert summary["warnings"] == []


def test_summary_rejects_missing_strategy_section():
    engine = AnalyticsEngine()

    with pytest.raises(ValueError):
        engine.build_backtest_validation_summary(
            {
                "benchmark_IHSG": {
                    "cumulative_return_pct": 4.25,
                },
            }
        )


def test_load_backtest_validation_returns_none_when_file_is_missing():
    engine = AnalyticsEngine()

    validation = engine.load_backtest_validation(
        "TICKER_THAT_DOES_NOT_EXIST"
    )

    assert validation is None