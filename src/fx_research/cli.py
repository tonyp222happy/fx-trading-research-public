from __future__ import annotations

import argparse

from .pipeline import run_experiment
from .concepts import check_idea
from .sample_data import generate_sample_csv


def main(argv=None):
    parser = argparse.ArgumentParser(prog="fx-research", description="Reproducible FX strategy research framework")
    sub = parser.add_subparsers(dest="command", required=True)

    p_sample = sub.add_parser("sample-data", help="Generate deterministic synthetic M5 sample data")
    p_sample.add_argument("--output", required=True)
    p_sample.add_argument("--seed", type=int, default=20260812)
    p_sample.add_argument("--days", type=int, default=120)

    p_check = sub.add_parser("check-idea", help="Compare an idea with a transparent concept catalog")
    p_check.add_argument("--idea", required=True)
    p_check.add_argument("--catalog", required=True)
    p_check.add_argument("--output")

    p_run = sub.add_parser("run", help="Run backtest, walk-forward, IC and reproducibility report")
    p_run.add_argument("--idea", required=True)
    p_run.add_argument("--config", required=True)

    args = parser.parse_args(argv)
    if args.command == "sample-data":
        path = generate_sample_csv(args.output, args.seed, args.days)
        print(f"Wrote synthetic sample data: {path}")
    elif args.command == "check-idea":
        result = check_idea(args.idea, args.catalog)
        if args.output:
            result.to_csv(args.output, index=False)
        print(result.head(10).to_string(index=False))
    elif args.command == "run":
        out = run_experiment(args.idea, args.config)
        print(f"Research run written to: {out}")


if __name__ == "__main__":
    main()
