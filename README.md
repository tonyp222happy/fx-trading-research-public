# FX Trading Research

A public, reproducible framework for testing FX trading hypotheses from **idea documentation through validation and reproducibility**.

This repository deliberately stops before platform-specific trading translation, broker integration, production verification, or live deployment. It is a clean public research layer, not a live trading system.

## Public research boundary

```text
Market data + strategy hypothesis + research configuration
        ↓
Concept review
        ↓
Executable strategy specification
        ↓
Python backtest
        ↓
Benchmark comparison
        ↓
Walk-forward validation
        ↓
Factor / IC analysis
        ↓
Documentation + reproducibility report
        ↓
STOP
```

Private/production concerns such as platform-specific trading translation, broker credentials, deployment scripts, server paths, and live execution are intentionally out of scope.

## Input contract

The framework is organized around three user inputs:

1. **Market data** — standard OHLC(V) CSV.
2. **Strategy hypothesis** — a Markdown idea document.
3. **Research configuration** — YAML that identifies the executable strategy adapter and testing assumptions.

The natural-language idea is the research record. It may originate from a manual observation, video, charting platform, community forum, article, research paper, or another source. Before backtesting, it must be normalized and translated into a deterministic Python strategy function. The example configuration points to a built-in educational strategy adapter; your own strategy can be referenced the same way. No AI service is required.

## Quick start

```bash
python -m pip install -e .[dev]

# Generate deterministic synthetic M5 sample data.
# This is demonstration data, not real market history.
fx-research sample-data --output examples/data/EURUSD_M5_sample.csv

# Transparent duplicate/concept check (no AI required).
fx-research check-idea \
  --idea examples/ideas/ma_breakout.md \
  --catalog examples/concept_catalog.csv

# Run the full public research pipeline.
fx-research run \
  --idea examples/ideas/ma_breakout.md \
  --config examples/configs/ma_breakout.yaml

# Run tests.
pytest -q
```

The run produces:

```text
runs/example_ma_breakout/
├── concept_review.md
├── config.resolved.yaml
├── data_manifest.json
├── strategy_source.py
├── trades.csv
├── equity.csv
├── metrics.json
├── walk_forward.csv
├── factor_ic.csv
└── reproducibility_report.md
```

## CSV format

Minimum columns:

```csv
datetime,open,high,low,close
2025-01-02 00:00:00,1.1030,1.1034,1.1028,1.1032
```

`volume` is optional. Column names are case-insensitive after loading. The experiment configuration must declare the timestamp timezone; the framework does not guess whether unlabeled timestamps are UTC, session time, source-local time, or another zone. See [docs/DATA_FORMAT.md](docs/DATA_FORMAT.md).

## Strategy interface

A strategy adapter receives a signal-timeframe OHLCV DataFrame and a parameter dictionary, and returns a DataFrame containing:

- `entry`: boolean signal generated from closed-bar information
- `signal_strength`: numeric factor value used for IC analysis

See [docs/STRATEGY_TEMPLATE.md](docs/STRATEGY_TEMPLATE.md) and `src/fx_research/strategies/example_ma_breakout.py`.

## Research principles

- Use closed bars; do not leak future information.
- Execute entries on the next bar, not the signal bar.
- Record execution assumptions explicitly.
- Benchmark every test against the same-period underlying return.
- Treat parameter searches as research, not proof.
- Use out-of-sample walk-forward evaluation.
- Preserve rejected ideas and negative results.
- Do not promote performance figures without a reproducibility manifest.

See [docs/IDEA_INGESTION.md](docs/IDEA_INGESTION.md), [docs/RESEARCH_PROCESS.md](docs/RESEARCH_PROCESS.md), [docs/COMBINATION_TESTING.md](docs/COMBINATION_TESTING.md), [docs/VALIDATION.md](docs/VALIDATION.md), [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md), and [docs/OPTIONAL_AI.md](docs/OPTIONAL_AI.md).

## Example strategy disclaimer

The included moving-average example exists only to demonstrate the framework. It is **not** a recommendation, production strategy, or representation of any private strategy implementation. Synthetic sample data is used so the example is redistributable and deterministic.

## Repository status

This package is prepared as **v0.1.0**. No software license has been selected in this release. Add an appropriate license separately if you decide to grant reuse rights. See [docs/PUBLICATION_CHECKLIST.md](docs/PUBLICATION_CHECKLIST.md).
