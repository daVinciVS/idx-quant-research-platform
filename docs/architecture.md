\# Architecture



\## Purpose



IDX Quant Research Platform is a Python-based research and decision-support project for Indonesian equities. It is designed to support reproducible analysis, data validation, technical screening, backtesting, and report generation.



It is not an automated trading system and does not provide investment advice.



\## Current system



The current implementation consists of script-based workflows:



\- `generate\_report.py` — Single-stock deep-dive analysis and report generation

\- `run\_screener.py` — Multi-stock screener workflow

\- `run\_predictor.py` — Technical scenario and volatility context

\- `backtest\_predictor.py` — Predictor validation and walk-forward analysis

\- `pdf\_reporter.py` — PDF report generation



\## Target architecture



```text

src/

├── data/           # Data ingestion, caching, manual input loaders, validation

├── analytics/      # Indicators, trend logic, scoring, trade-plan calculations

├── research/       # Backtesting, performance measurement, experiment tracking

├── reporting/      # Excel, PDF, charts, and report data models

├── workflows/      # Single-stock, screener, predictor, and backtest orchestration

└── config/         # Typed configuration and environment-variable handling



tests/

├── unit/           # Pure logic and calculation tests

├── integration/    # Data-to-report workflow tests

└── fixtures/       # Synthetic and non-sensitive test inputs



docs/

├── architecture.md

├── data-contracts.md

└── methodology.md

```



\## Engineering principles



\- Use completed daily candles only.

\- Normalize market dates to Jakarta trading-session dates.

\- Prevent look-ahead bias in all research and backtests.

\- Keep credentials, private data, caches, and generated reports out of version control.

\- Separate data ingestion, analysis logic, workflows, and reporting.

\- Treat predictor outputs as scenarios, not probability forecasts.

\- Store model and data assumptions alongside research results.

\- Add tests before refactoring business-critical behavior.



\## Initial test priorities



1\. A timestamp must normalize to the correct Jakarta calendar date.

2\. An incomplete current-day daily candle must be excluded.

3\. Indicator calculations must respect their required lookback periods.

4\. Trade-plan stop-loss and position-risk calculations must be reproducible.

5\. Backtests must not access data later than their signal date.

