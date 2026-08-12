from __future__ import annotations

from itertools import product

import pandas as pd

from .engine import run_backtest
from .metrics import compute_metrics
from .strategy import validate_signal_frame


def _grid(grid: dict):
    if not grid:
        yield {}
        return
    keys = list(grid)
    for vals in product(*(grid[k] for k in keys)):
        yield dict(zip(keys, vals))


def _score(metrics: dict) -> float:
    # Simple predeclared training objective for the educational implementation.
    return float(metrics["total_return"] - 2.0 * abs(metrics["floating_max_drawdown"]))


def run_walk_forward(data: pd.DataFrame, strategy_fn, base_params: dict, backtest_cfg: dict, cfg: dict) -> pd.DataFrame:
    train_days = int(cfg["train_days"]); test_days = int(cfg["test_days"]); step_days = int(cfg["step_days"])
    grid = cfg.get("parameter_grid", {})
    if min(train_days, test_days, step_days) <= 0:
        raise ValueError("walk_forward day values must be positive")

    rows = []
    start = data.index.min()
    end = data.index.max()
    fold = 0
    while True:
        train_start = start + pd.Timedelta(days=fold * step_days)
        train_end = train_start + pd.Timedelta(days=train_days)
        test_end = train_end + pd.Timedelta(days=test_days)
        if test_end > end:
            break
        train = data[(data.index >= train_start) & (data.index < train_end)]
        # Keep training history available to rolling indicators for the OOS signal calculation.
        test_context = data[(data.index >= train_start) & (data.index < test_end)]
        test = data[(data.index >= train_end) & (data.index < test_end)]
        if len(train) < 10 or len(test) < 2:
            fold += 1
            continue

        best = None
        for candidate in _grid(grid):
            params = {**base_params, **candidate}
            try:
                sig = validate_signal_frame(train, strategy_fn(train, params))
                tr, eq = run_backtest(train, sig, backtest_cfg)
                met = compute_metrics(train, tr, eq, float(backtest_cfg.get("starting_equity", 10000)))
            except ValueError:
                continue
            score = _score(met)
            if best is None or score > best[0]:
                best = (score, params, met)
        if best is None:
            fold += 1
            continue

        _, best_params, train_metrics = best
        ctx_sig = validate_signal_frame(test_context, strategy_fn(test_context, best_params))
        test_sig = ctx_sig.loc[test.index]
        tr, eq = run_backtest(test, test_sig, backtest_cfg)
        test_metrics = compute_metrics(test, tr, eq, float(backtest_cfg.get("starting_equity", 10000)))
        rows.append({
            "fold": fold + 1,
            "train_start": str(train.index.min()),
            "train_end": str(train.index.max()),
            "test_start": str(test.index.min()),
            "test_end": str(test.index.max()),
            "best_params": str(best_params),
            "train_score": _score(train_metrics),
            "train_total_return": train_metrics["total_return"],
            "train_benchmark_return": train_metrics["benchmark_return"],
            "train_alpha_total_return": train_metrics["alpha_total_return"],
            "train_max_dd": train_metrics["floating_max_drawdown"],
            "test_trades": test_metrics["trades"],
            "test_total_return": test_metrics["total_return"],
            "test_benchmark_return": test_metrics["benchmark_return"],
            "test_alpha_total_return": test_metrics["alpha_total_return"],
            "test_max_dd": test_metrics["floating_max_drawdown"],
            "test_profit_factor": test_metrics["profit_factor"],
        })
        fold += 1
    return pd.DataFrame(rows)
