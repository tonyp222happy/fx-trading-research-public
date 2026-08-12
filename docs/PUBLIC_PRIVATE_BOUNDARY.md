# Public / Private Boundary

## Public

- research methodology
- CSV loaders and resampling
- generic backtest engine
- benchmark metrics
- walk-forward tooling
- factor / IC analysis
- templates and example strategy
- deterministic synthetic sample data generator
- reproducibility reporting
- tests and CI

## Keep private unless explicitly approved

- current production strategy implementation
- platform-specific trading code and translation/deployment logic
- broker or account configuration
- credentials / API tokens
- VPS paths and operational infrastructure
- live trade logs that expose private information
- proprietary market datasets
- internal research artifacts you do not intend to release

The public repository should be a curated derivative, not a history-preserving mirror of a private research workspace.
