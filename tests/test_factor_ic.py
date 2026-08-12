import pandas as pd

from fx_research.factor_ic import compute_factor_ic


def test_factor_ic_returns_row():
    idx = pd.date_range("2025-01-01", periods=20, freq="15min")
    close = pd.Series(range(100, 120), index=idx, dtype=float)
    data = pd.DataFrame({"close": close})
    strength = pd.Series(range(20), index=idx, dtype=float)
    out = compute_factor_ic(data, strength, [1, 2])
    assert list(out["horizon_bars"]) == [1, 2]
    assert (out["observations"] > 0).all()
