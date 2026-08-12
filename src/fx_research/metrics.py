from __future__ import annotations

import math

import numpy as np
import pandas as pd


def max_drawdown(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    peak = series.cummax()
    dd = series / peak - 1.0
    return float(dd.min())


def _daily_returns(equity: pd.Series) -> pd.Series:
    if equity.empty:
        return pd.Series(dtype=float)
    daily = equity.resample("1D").last().dropna()
    return daily.pct_change().dropna()


def compute_metrics(data: pd.DataFrame, trades: pd.DataFrame, equity: pd.DataFrame, starting_equity: float) -> dict:
    final_equity = float(equity["equity"].iloc[-1]) if len(equity) else float(starting_equity)
    total_return = final_equity / starting_equity - 1.0
    if len(data) >= 2:
        days = max((data.index[-1] - data.index[0]).total_seconds() / 86400.0, 1.0)
        cagr = (final_equity / starting_equity) ** (365.25 / days) - 1.0 if final_equity > 0 else -1.0
        benchmark_return = float(data["close"].iloc[-1] / data["close"].iloc[0] - 1.0)
    else:
        days, cagr, benchmark_return = 0.0, 0.0, 0.0

    pnls = trades["pnl"] if "pnl" in trades else pd.Series(dtype=float)
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]
    pf = float(wins.sum() / abs(losses.sum())) if len(losses) and abs(losses.sum()) > 0 else (float("inf") if len(wins) else 0.0)
    win_rate = float((pnls > 0).mean()) if len(pnls) else 0.0

    floating_dd = max_drawdown(equity["equity"]) if len(equity) else 0.0
    realized_dd = max_drawdown(equity["realized_equity"]) if len(equity) else 0.0
    daily = _daily_returns(equity["equity"]) if len(equity) else pd.Series(dtype=float)
    sharpe = float(np.sqrt(252) * daily.mean() / daily.std(ddof=1)) if len(daily) > 1 and daily.std(ddof=1) > 0 else 0.0
    downside = daily[daily < 0]
    sortino = float(np.sqrt(252) * daily.mean() / downside.std(ddof=1)) if len(downside) > 1 and downside.std(ddof=1) > 0 else 0.0
    calmar = float(cagr / abs(floating_dd)) if floating_dd < 0 else 0.0

    return {
        "trades": int(len(trades)),
        "win_rate": win_rate,
        "profit_factor": pf,
        "starting_equity": float(starting_equity),
        "final_equity": final_equity,
        "total_return": total_return,
        "cagr": float(cagr),
        "realized_max_drawdown": realized_dd,
        "floating_max_drawdown": floating_dd,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "benchmark_return": benchmark_return,
        "alpha_total_return": total_return - benchmark_return,
        "test_days": days,
    }
