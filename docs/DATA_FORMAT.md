# Data Format

## Required schema

CSV files must contain:

- `datetime`
- `open`
- `high`
- `low`
- `close`

`volume` is optional.

The experiment configuration must also declare the timestamp timezone. Do not assume that an unlabeled timestamp is UTC, exchange time, broker time, or local time.

Example:

```yaml
data:
  path: data/example.csv
  source: user_supplied
  datetime_column: datetime
  timezone: UTC
  signal_timeframe: 15min
```

The loader:

1. normalizes column names to lowercase,
2. parses `datetime`,
3. localizes naive timestamps to the declared timezone or converts aware timestamps to it,
4. sorts timestamps,
5. rejects duplicate timestamps,
6. verifies OHLC consistency, and
7. optionally resamples to the configured signal timeframe.

## Resampling

For OHLCV resampling:

- open = first
- high = max
- low = min
- close = last
- volume = sum

Incomplete intervals are not specially repaired. Users are responsible for understanding missing bars, market sessions, daylight-saving changes, and source-specific timestamps.

## Data provenance

For reproducibility, record:

- the data source or acquisition method,
- the local input path,
- declared timezone,
- exact file SHA-256,
- first and last evaluated timestamps,
- row counts before and after resampling.

## Public data policy

Do not commit market data unless you have redistribution rights. The repository therefore generates deterministic synthetic sample data for tests and demonstrations.
