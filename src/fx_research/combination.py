from __future__ import annotations

import pandas as pd


def combine_signal_frames(frames: list[pd.DataFrame], method: str = "union") -> pd.DataFrame:
    """Combine compatible strategy outputs without changing the backtest engine.

    union: enter when any strategy enters.
    intersection: enter only when every strategy enters.
    signal_strength is the row-wise mean of available factor values.
    """
    if not frames:
        raise ValueError("At least one signal frame is required")
    base_index = frames[0].index
    if any(not f.index.equals(base_index) for f in frames):
        raise ValueError("All signal frames must share the same index")
    entries = pd.concat([f["entry"].astype(bool) for f in frames], axis=1)
    strengths = pd.concat([pd.to_numeric(f["signal_strength"], errors="coerce") for f in frames], axis=1)
    if method == "union":
        entry = entries.any(axis=1)
    elif method == "intersection":
        entry = entries.all(axis=1)
    else:
        raise ValueError("method must be union or intersection")
    return pd.DataFrame({"entry": entry, "signal_strength": strengths.mean(axis=1)}, index=base_index)
