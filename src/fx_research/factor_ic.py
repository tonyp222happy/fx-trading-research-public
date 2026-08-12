from __future__ import annotations

import pandas as pd


def compute_factor_ic(data: pd.DataFrame, signal_strength: pd.Series, horizons_bars: list[int]) -> pd.DataFrame:
    rows = []
    strength = pd.to_numeric(signal_strength, errors="coerce")
    for horizon in horizons_bars:
        h = int(horizon)
        if h <= 0:
            raise ValueError("Factor IC horizons must be positive integers")
        forward = data["close"].shift(-h) / data["close"] - 1.0
        pair = pd.concat([strength.rename("strength"), forward.rename("forward")], axis=1).dropna()
        if len(pair) >= 3:
            strength_rank = pair["strength"].rank(method="average")
            forward_rank = pair["forward"].rank(method="average")
            ic = float(strength_rank.corr(forward_rank))
        else:
            ic = float("nan")
        rows.append({"horizon_bars": h, "observations": int(len(pair)), "spearman_ic": ic})
    return pd.DataFrame(rows)
