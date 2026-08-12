from __future__ import annotations

import importlib
from typing import Callable

import pandas as pd


def load_strategy_callable(spec: str) -> Callable[[pd.DataFrame, dict], pd.DataFrame]:
    if ":" not in spec:
        raise ValueError("strategy.callable must use module:function format")
    module_name, function_name = spec.split(":", 1)
    module = importlib.import_module(module_name)
    fn = getattr(module, function_name)
    if not callable(fn):
        raise TypeError(f"Strategy target is not callable: {spec}")
    return fn


def validate_signal_frame(data: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
    if not signals.index.equals(data.index):
        raise ValueError("Strategy output index must exactly match data index")
    for col in ("entry", "signal_strength"):
        if col not in signals.columns:
            raise ValueError(f"Strategy output missing required column: {col}")
    out = signals[["entry", "signal_strength"]].copy()
    out["entry"] = out["entry"].fillna(False).astype(bool)
    out["signal_strength"] = pd.to_numeric(out["signal_strength"], errors="coerce")
    return out
