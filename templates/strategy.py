import pandas as pd


def generate_signals(data: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Return closed-bar entry signals and a numeric factor value."""
    out = pd.DataFrame(index=data.index)
    out["entry"] = False
    out["signal_strength"] = 0.0
    return out
