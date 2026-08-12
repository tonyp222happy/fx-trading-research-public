import pandas as pd

from fx_research.walk_forward import run_walk_forward


def _strategy(data, params):
    fast = data["close"].rolling(int(params["fast"]), min_periods=int(params["fast"])).mean()
    slow = data["close"].rolling(int(params["slow"]), min_periods=int(params["slow"])).mean()
    entry = (fast > slow) & (fast.shift(1) <= slow.shift(1))
    return pd.DataFrame({"entry": entry.fillna(False), "signal_strength": (fast - slow).fillna(0.0)}, index=data.index)


def test_walk_forward_records_oos_benchmark_columns():
    idx = pd.date_range("2025-01-01", periods=24 * 4 * 90, freq="15min", tz="UTC")
    close = pd.Series(100.0 + (pd.Series(range(len(idx)), dtype=float).values * 0.0005), index=idx)
    data = pd.DataFrame({
        "open": close,
        "high": close * 1.001,
        "low": close * 0.999,
        "close": close,
    }, index=idx)
    out = run_walk_forward(
        data,
        _strategy,
        {"fast": 4, "slow": 12},
        {
            "starting_equity": 10000,
            "risk_fraction": 0.01,
            "stop_pct": 0.01,
            "take_profit_pct": 0.02,
            "max_hold_bars": 16,
            "commission_bps": 0,
            "slippage_bps": 0,
            "intrabar_priority": "stop_first",
        },
        {
            "train_days": 30,
            "test_days": 10,
            "step_days": 10,
            "parameter_grid": {"fast": [4], "slow": [12]},
        },
    )
    assert len(out) > 0
    assert {"test_benchmark_return", "test_alpha_total_return"}.issubset(out.columns)
