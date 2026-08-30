# Public Demo Data

This directory is reserved for small, reproducible, public-safe datasets used
by the IDX Quant Research Platform demo experience.

## Privacy policy

Only curated data that is safe to publish belongs here.

Do not add:

- Personal portfolio configuration or holdings.
- Brokerage statements, account balances, or order history.
- API keys, tokens, or credentials.
- Local watchlists.
- Raw caches or manually maintained market files.
- Generated reports that include private data.

Private local data remains under `data/` and is ignored by Git by default.

## Current demo cases

The first public demo uses deterministic code fixtures exposed through:

```text
src/application/public_demo.py
```

The cases demonstrate:

- `avoid`
- `watchlist`
- `consider_entry`
- `reduced_size`
- `insufficient_data`

Future committed historical fixtures must be anonymized or sourced from
publicly shareable market data, documented with their origin and as-of date,
and kept deliberately small.