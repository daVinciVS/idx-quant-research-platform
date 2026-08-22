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

