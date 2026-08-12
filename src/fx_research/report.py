from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def git_commit() -> str:
    # Generic CI override first; local Git is the normal fallback.
    if os.getenv("CI_COMMIT_SHA"):
        return os.environ["CI_COMMIT_SHA"]
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unavailable"


def _package_version() -> str:
    try:
        return version("fx-trading-research")
    except PackageNotFoundError:
        from . import __version__
        return __version__


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _clean_for_json(obj):
    if isinstance(obj, dict):
        return {k: _clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_for_json(v) for v in obj]
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return str(obj)
    return obj


def write_report(
    out_dir: Path,
    idea_path: Path,
    config: dict,
    data_manifest: dict,
    strategy_spec: str,
    metrics: dict,
    validation: dict,
    wf: pd.DataFrame,
    ic: pd.DataFrame,
    command: str,
):
    bt = config["backtest"]
    lines = [
        "# Reproducibility Report", "",
        f"- Experiment: `{config['experiment']['name']}`",
        f"- Framework version: `{_package_version()}`",
        f"- Version-control commit: `{git_commit()}`",
        f"- Strategy callable: `{strategy_spec}`",
        f"- Idea SHA-256: `{_sha256(idea_path)}`",
        f"- Data source: `{data_manifest.get('source', 'unspecified')}`",
        f"- Data path: `{data_manifest['path']}`",
        f"- Data SHA-256: `{data_manifest['sha256']}`",
        f"- Declared timezone: `{data_manifest['timezone']}`",
        f"- Data rows (raw): {data_manifest['raw_rows']}",
        f"- Data rows (signal timeframe): {data_manifest['signal_rows']}",
        f"- Evaluated range: {data_manifest['evaluation_start']} → {data_manifest['evaluation_end']}",
        f"- Signal timeframe: `{data_manifest['signal_timeframe']}`",
        f"- Python: `{platform.python_version()}`",
        f"- pandas: `{pd.__version__}`",
        f"- numpy: `{np.__version__}`",
        f"- YAML parser: `{getattr(yaml, '__version__', 'unknown')}`",
        "",
        "## Reproduction command", "", "```bash", command, "```", "",
        "## Execution assumptions", "",
        "- Signals are computed on closed bars.",
        "- Entries execute on the next bar open.",
        f"- Starting equity: `{bt.get('starting_equity', 10000)}`.",
        f"- Risk fraction per trade: `{bt.get('risk_fraction')}`.",
        f"- Stop distance: `{bt.get('stop_pct')}` of entry price.",
        f"- Take-profit distance: `{bt.get('take_profit_pct')}` of entry price.",
        f"- Maximum holding period: `{bt.get('max_hold_bars')}` signal bars.",
        f"- Intrabar stop/target priority: `{bt.get('intrabar_priority', 'stop_first')}`.",
        f"- Commission: `{bt.get('commission_bps', 0)} bps` per side.",
        f"- Slippage: `{bt.get('slippage_bps', 0)} bps` per side.",
        "",
        "## Strategy parameters", "", "```yaml",
        yaml.safe_dump(config.get("strategy", {}).get("params", {}), sort_keys=True).rstrip(),
        "```", "",
        "## Main metrics", "",
    ]
    for k, v in metrics.items():
        lines.append(f"- {k}: `{v}`")

    lines += ["", "## Validation gates", ""]
    for k, v in validation.items():
        lines.append(f"- {k}: `{v}`")

    lines += ["", "## Walk-forward", "", f"Folds: `{len(wf)}`"]
    if len(wf):
        for _, row in wf.iterrows():
            lines.append(
                f"- Fold {int(row['fold'])}: OOS return `{row['test_total_return']}`, "
                f"benchmark `{row['test_benchmark_return']}`, alpha `{row['test_alpha_total_return']}`, "
                f"max DD `{row['test_max_dd']}`, trades `{int(row['test_trades'])}`"
            )

    lines += ["", "## Factor IC", "", f"Horizons evaluated: `{len(ic)}`"]
    if len(ic):
        for _, row in ic.iterrows():
            lines.append(
                f"- Horizon {int(row['horizon_bars'])} bars: Spearman IC `{row['spearman_ic']}`, "
                f"observations `{int(row['observations'])}`"
            )

    lines += [
        "", "## Research record", "",
        f"Original idea file: `{idea_path}`",
        "",
        "Resolved configuration is stored in `config.resolved.yaml`; the exact executable strategy function is stored in `strategy_source.py`.",
        "",
        "This report is evidence for reproducibility of this run, not a claim of future profitability.",
    ]
    (out_dir / "reproducibility_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
