from __future__ import annotations

import inspect
import json
import shutil
from pathlib import Path

import yaml

from .data import file_sha256, load_ohlcv_csv, resample_ohlcv
from .engine import run_backtest
from .factor_ic import compute_factor_ic
from .metrics import compute_metrics
from .report import write_report
from .strategy import load_strategy_callable, validate_signal_frame
from .walk_forward import run_walk_forward


def _validation(metrics: dict, cfg: dict) -> dict:
    min_trades = int(cfg.get("minimum_trades", 0))
    max_dd = float(cfg.get("maximum_drawdown", 1.0))
    return {
        "minimum_trades_required": min_trades,
        "minimum_trades_pass": metrics["trades"] >= min_trades,
        "maximum_drawdown_allowed": max_dd,
        "maximum_drawdown_pass": abs(metrics["floating_max_drawdown"]) <= max_dd,
    }


def run_experiment(idea_path: str | Path, config_path: str | Path) -> Path:
    idea_path = Path(idea_path)
    config_path = Path(config_path)
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    out = Path(cfg["experiment"].get("output_dir", f"runs/{cfg['experiment']['name']}"))
    out.mkdir(parents=True, exist_ok=True)

    data_cfg = cfg["data"]
    raw_path = Path(data_cfg["path"])
    timezone = data_cfg.get("timezone")
    if not timezone:
        raise ValueError("data.timezone is required for reproducible timestamp handling")
    raw = load_ohlcv_csv(raw_path, data_cfg.get("datetime_column", "datetime"), timezone=timezone)
    data = resample_ohlcv(raw, data_cfg.get("signal_timeframe", "15min"))

    strategy_spec = cfg["strategy"]["callable"]
    strategy_fn = load_strategy_callable(strategy_spec)
    params = dict(cfg["strategy"].get("params", {}))
    signals = validate_signal_frame(data, strategy_fn(data.copy(), params))

    trades, equity = run_backtest(data, signals, cfg["backtest"])
    metrics = compute_metrics(data, trades, equity, float(cfg["backtest"].get("starting_equity", 10000)))
    validation = _validation(metrics, cfg.get("validation", {}))

    wf_cfg = cfg.get("walk_forward", {})
    wf = run_walk_forward(data, strategy_fn, params, cfg["backtest"], wf_cfg) if wf_cfg.get("enabled", False) else __import__('pandas').DataFrame()
    ic_cfg = cfg.get("factor_ic", {})
    ic = compute_factor_ic(data, signals["signal_strength"], list(ic_cfg.get("horizons_bars", []))) if ic_cfg.get("enabled", False) else __import__('pandas').DataFrame()

    data_manifest = {
        "path": str(raw_path),
        "source": data_cfg.get("source", "user_supplied"),
        "timezone": timezone,
        "sha256": file_sha256(raw_path),
        "raw_rows": int(len(raw)),
        "signal_rows": int(len(data)),
        "signal_timeframe": data_cfg.get("signal_timeframe", "15min"),
        "evaluation_start": str(data.index.min()),
        "evaluation_end": str(data.index.max()),
    }

    shutil.copy2(idea_path, out / "idea.md")
    concept = (
        "# Concept Review\n\n## Source hypothesis\n\n"
        + idea_path.read_text(encoding="utf-8")
        + "\n\n## Implementation binding\n\n"
        + f"Executable strategy: `{strategy_spec}`\n"
    )
    (out / "concept_review.md").write_text(concept, encoding="utf-8")
    (out / "config.resolved.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    (out / "data_manifest.json").write_text(json.dumps(data_manifest, indent=2), encoding="utf-8")
    (out / "strategy_source.py").write_text(inspect.getsource(strategy_fn), encoding="utf-8")
    trades.to_csv(out / "trades.csv", index=False)
    equity.to_csv(out / "equity.csv")
    (out / "metrics.json").write_text(json.dumps({"metrics": metrics, "validation": validation}, indent=2, allow_nan=True), encoding="utf-8")
    wf.to_csv(out / "walk_forward.csv", index=False)
    ic.to_csv(out / "factor_ic.csv", index=False)
    command = f"fx-research run --idea {idea_path} --config {config_path}"
    write_report(out, idea_path, cfg, data_manifest, strategy_spec, metrics, validation, wf, ic, command)
    return out
