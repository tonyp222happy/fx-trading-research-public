from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def generate_sample_csv(path: str | Path, seed: int = 20260812, days: int = 120) -> Path:
    """Generate deterministic synthetic M5 OHLCV data for demos/tests."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    full = pd.date_range("2024-01-01", periods=days * 24 * 12, freq="5min")
    idx = full[full.dayofweek < 5]
    rng = np.random.default_rng(seed)
    n = len(idx)
    phase = np.linspace(0, 14 * np.pi, n)
    drift = 0.000004 * np.sin(phase) + 0.000001
    noise = rng.normal(0, 0.00011, n)
    log_close = np.log(1.10) + np.cumsum(drift + noise)
    close = np.exp(log_close)
    open_ = np.r_[close[0], close[:-1]]
    spread = np.abs(rng.normal(0.00008, 0.000025, n)) + 0.00002
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    volume = rng.integers(50, 500, n)
    df = pd.DataFrame({
        "datetime": idx, "open": open_, "high": high, "low": low, "close": close, "volume": volume
    })
    df.to_csv(path, index=False, float_format="%.8f")
    return path
