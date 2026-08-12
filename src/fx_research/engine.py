from __future__ import annotations

import math
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd


@dataclass
class Trade:
    signal_time: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    units: float
    pnl: float
    return_pct_on_entry: float
    equity_after: float
    exit_reason: str
    bars_held: int


def _apply_bps(price: float, bps: float, side: str) -> float:
    adj = bps / 10000.0
    return price * (1 + adj if side == "buy" else 1 - adj)


def run_backtest(data: pd.DataFrame, signals: pd.DataFrame, cfg: dict):
    """Long-only, one-position research engine.

    Signal on bar t is executed at bar t+1 open. When stop and target are both
    touched in one bar, the configured priority resolves the unknown intrabar path.
    """
    starting_equity = float(cfg.get("starting_equity", 10000))
    risk_fraction = float(cfg.get("risk_fraction", 0.01))
    stop_pct = float(cfg.get("stop_pct", 0.005))
    take_profit_pct = float(cfg.get("take_profit_pct", 0.01))
    max_hold = int(cfg.get("max_hold_bars", 96))
    commission_bps = float(cfg.get("commission_bps", 0.0))
    slippage_bps = float(cfg.get("slippage_bps", 0.0))
    priority = cfg.get("intrabar_priority", "stop_first")
    if priority not in {"stop_first", "target_first"}:
        raise ValueError("intrabar_priority must be stop_first or target_first")
    if not (0 < risk_fraction <= 1 and stop_pct > 0 and take_profit_pct > 0):
        raise ValueError("Invalid risk/stop/target configuration")

    cash = starting_equity
    position = None
    trades: list[Trade] = []
    equity_rows = []

    entry_signal = signals["entry"].fillna(False).astype(bool)
    for i, (ts, row) in enumerate(data.iterrows()):
        # Enter only at next bar open after a closed-bar signal.
        if position is None and i > 0 and bool(entry_signal.iloc[i - 1]):
            raw_entry = float(row["open"])
            entry_price = _apply_bps(raw_entry, slippage_bps, "buy")
            risk_amount = cash * risk_fraction
            stop_distance = entry_price * stop_pct
            units = risk_amount / stop_distance
            entry_commission = entry_price * units * commission_bps / 10000.0
            cash -= entry_commission
            position = {
                "signal_time": data.index[i - 1],
                "entry_time": ts,
                "entry_price": entry_price,
                "units": units,
                "stop": entry_price * (1 - stop_pct),
                "target": entry_price * (1 + take_profit_pct),
                "bars": 0,
                "entry_equity": cash,
            }

        if position is not None:
            position["bars"] += 1
            hit_stop = float(row["low"]) <= position["stop"]
            hit_target = float(row["high"]) >= position["target"]
            reason = None
            raw_exit = None
            if hit_stop and hit_target:
                if priority == "stop_first":
                    raw_exit, reason = position["stop"], "STOP"
                else:
                    raw_exit, reason = position["target"], "TARGET"
            elif hit_stop:
                raw_exit, reason = position["stop"], "STOP"
            elif hit_target:
                raw_exit, reason = position["target"], "TARGET"
            elif position["bars"] >= max_hold:
                raw_exit, reason = float(row["close"]), "MAX_HOLD"

            if reason is not None:
                exit_price = _apply_bps(float(raw_exit), slippage_bps, "sell")
                gross_pnl = (exit_price - position["entry_price"]) * position["units"]
                exit_commission = exit_price * position["units"] * commission_bps / 10000.0
                pnl = gross_pnl - exit_commission
                cash += pnl
                trades.append(Trade(
                    signal_time=str(position["signal_time"]),
                    entry_time=str(position["entry_time"]),
                    exit_time=str(ts),
                    entry_price=position["entry_price"],
                    exit_price=exit_price,
                    units=position["units"],
                    pnl=pnl,
                    return_pct_on_entry=(exit_price / position["entry_price"] - 1) * 100,
                    equity_after=cash,
                    exit_reason=reason,
                    bars_held=position["bars"],
                ))
                position = None

        floating_equity = cash
        if position is not None:
            floating_equity += (float(row["close"]) - position["entry_price"]) * position["units"]
        equity_rows.append({"datetime": ts, "equity": floating_equity, "realized_equity": cash})

    # Force-close an open position at the final close so every run is self-contained.
    if position is not None and len(data):
        ts = data.index[-1]
        raw_exit = float(data.iloc[-1]["close"])
        exit_price = _apply_bps(raw_exit, slippage_bps, "sell")
        gross_pnl = (exit_price - position["entry_price"]) * position["units"]
        exit_commission = exit_price * position["units"] * commission_bps / 10000.0
        pnl = gross_pnl - exit_commission
        cash += pnl
        trades.append(Trade(
            signal_time=str(position["signal_time"]),
            entry_time=str(position["entry_time"]),
            exit_time=str(ts),
            entry_price=position["entry_price"],
            exit_price=exit_price,
            units=position["units"],
            pnl=pnl,
            return_pct_on_entry=(exit_price / position["entry_price"] - 1) * 100,
            equity_after=cash,
            exit_reason="END_OF_DATA",
            bars_held=position["bars"],
        ))
        equity_rows[-1]["equity"] = cash
        equity_rows[-1]["realized_equity"] = cash

    trade_df = pd.DataFrame([asdict(t) for t in trades])
    equity_df = pd.DataFrame(equity_rows).set_index("datetime") if equity_rows else pd.DataFrame(columns=["equity", "realized_equity"])
    return trade_df, equity_df
