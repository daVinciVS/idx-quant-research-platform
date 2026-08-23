\# Test Plan



\## Goal



Protect the platform from financial-data and research errors during refactoring.



\## Test levels



| Level | Scope | Example |

|---|---|---|

| Unit | One deterministic function | ATR calculation from fixed OHLC data |

| Integration | Several project components | Normalized daily data passed to a screener |

| Regression | A previous bug remains fixed | Jakarta date does not shift backward |

| Research validation | Statistical workflow | Backtest does not use future prices |



\## Initial regression tests



\### Jakarta daily date normalization



Given a timestamp returned by a market-data provider, the platform must derive the intended Asia/Jakarta trading calendar date without shifting it one day backward.



\### Incomplete daily candle exclusion



If the current Jakarta trading session is still open, the current daily bar must not be included in daily indicators, signal generation, screening, or reports.



\## Test data policy



Tests use synthetic OHLCV data or non-sensitive fixture data only. They must not depend on live APIs, broker exports, private foreign-flow data, or local credentials.



\## Definition of done



A behavior change is complete when:



1\. The relevant test passes locally.

2\. The full test suite passes.

3\. A commit records the change.

4\. The branch is pushed to GitHub.

## Manual smoke-test record

### 2026-08-24 — Single-stock workflow

- Command: `python .\generate_report.py`
- Workflow: `1` — Single Stock Deep-Dive Report
- Ticker: `BBCA`
- Data source: Yahoo-only analysis
- Result: Passed

Validation observed:

- Yahoo Finance daily price data loaded successfully.
- IHSG benchmark data loaded successfully.
- 479 daily records were processed.
- Indicators and report metrics were calculated.
- The Excel dashboard report was generated successfully.
- The PDF summary was generated successfully.
- No errors occurred in Jakarta date normalization, session-aware candle filtering, or DataFrame handling.

This smoke test supplements the automated unit-test suite; it does not replace integration tests.

### 2026-08-24 — Trade-plan module integration

- Command: `python .\generate_report.py`
- Workflow: `1` — Single Stock Deep-Dive Report
- Ticker: `BBCA`
- Data source: Yahoo-only analysis
- Result: Passed

Validation observed:

- `src.analytics.trade_plan.calculate_trade_plan()` was integrated into
  `AnalyticsEngine.calculate_metrics()`.
- The report ran successfully with valid ATR, resistance, and six-month-high inputs.
- Pullback and breakout plan fields were available to the report workflow.
- Excel dashboard report was generated successfully.
- PDF summary was generated successfully.
- No errors occurred in trade-plan calculation, report generation, or
  output handling.

Automated validation:

- `python -m pytest -v` → 29 passed
- `python -m py_compile .\generate_report.py` → passed