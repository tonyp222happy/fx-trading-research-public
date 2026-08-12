# Strategy Adapter Contract

A strategy adapter must expose a function with this shape:

```python
def generate_signals(data, params):
    # data: DataFrame indexed by datetime, with OHLC(V) columns
    # params: dict from YAML config
    # return: DataFrame with the same index and two columns
    return signals  # columns: entry, signal_strength
```

## Timing rule

`entry[t]` must use only information available by the close of bar `t`. The backtest engine executes a valid signal at the **next bar open**.

Do not shift future prices backward into the strategy.

## Example

```python
fast = data["close"].rolling(20).mean()
slow = data["close"].rolling(60).mean()
entry = (fast > slow) & (fast.shift(1) <= slow.shift(1))
strength = (fast - slow) / data["close"]
```

The public example is intentionally simple and is not intended as a profitable trading recommendation.
