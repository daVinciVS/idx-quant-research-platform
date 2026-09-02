# Demo Market-Data Fixtures

This directory contains small, deterministic OHLCV fixtures for the public
demo experience.

## Data policy

The fixtures are synthetic, market-shaped examples created only to demonstrate
the charting, trade-plan, decision, and paper-portfolio workflow.

They are not:

- Live market data.
- Historical prices for an actual IDX-listed company.
- A backtest dataset.
- A performance claim.
- Investment advice.

## Fixture format

Each CSV file must contain these columns:

```text
Date,Open,High,Low,Close,Volume
```

The public fixture loader validates:

- At least 80 daily rows.
- Increasing valid dates.
- Complete numeric OHLCV values.
- Positive prices.
- Non-negative volume.
- Valid high/low price ranges.

## Naming convention

A fixture filename maps to a public demo case:

```text
demo_entry_setup.csv
```

The UI will explicitly label all fixtures as synthetic demonstration data.