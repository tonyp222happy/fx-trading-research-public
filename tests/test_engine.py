import pandas as pd

from fx_research.engine import run_backtest


def test_signal_executes_next_bar_not_same_bar():
    idx = pd.date_range("2025-01-01", periods=3, freq="15min")
    data = pd.DataFrame({
        "open": [100, 101, 101], "high": [100.5, 102, 102], "low": [99.5, 100.5, 100.5], "close": [100, 101, 101]
    }, index=idx)
    sig = pd.DataFrame({"entry": [True, False, False], "signal_strength": [1,0,0]}, index=idx)
    trades, _ = run_backtest(data, sig, {
        "starting_equity": 10000, "risk_fraction": 0.01, "stop_pct": 0.01, "take_profit_pct": 0.01,
        "max_hold_bars": 1, "commission_bps": 0, "slippage_bps": 0, "intrabar_priority": "stop_first"
    })
    assert len(trades) == 1
    assert trades.iloc[0]["entry_time"].startswith(str(idx[1].date()))
    assert float(trades.iloc[0]["entry_price"]) == 101.0
