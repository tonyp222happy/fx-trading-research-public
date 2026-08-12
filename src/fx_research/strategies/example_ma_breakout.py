from __future__ import annotations

import pandas as pd


def generate_signals(data: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Educational MA crossover using only closed-bar information."""
    fast_n = int(params.get("fast_ma", 20))
    slow_n = int(params.get("slow_ma", 60))
    if fast_n <= 1 or slow_n <= 1 or fast_n >= slow_n:
        raise ValueError("Require 1 < fast_ma < slow_ma")

    fast = data["close"].rolling(fast_n, min_periods=fast_n).mean()
    slow = data["close"].rolling(slow_n, min_periods=slow_n).mean()
    cross_up = (fast > slow) & (fast.shift(1) <= slow.shift(1))

    out = pd.DataFrame(index=data.index)
    out["entry"] = cross_up.fillna(False)
    out["signal_strength"] = ((fast - slow) / data["close"]).astype(float)
    return out
