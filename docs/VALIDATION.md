# Validation

Validation is a process, not a single performance threshold.

## Core checks

- Sufficient trade count for the stated conclusion.
- Max drawdown within a predeclared research limit.
- Positive benchmark-relative evidence when relevant.
- No look-ahead or same-bar signal/entry leakage.
- Stable behavior across different periods.
- Explicit costs and fill assumptions.
- Explicit timezone and session assumptions.

The example configuration includes `minimum_trades` and `maximum_drawdown` only as demonstration gates. They are not universal investment rules.

## Benchmarking

The main backtest records the same-period underlying return and strategy return minus that benchmark. Walk-forward output also records benchmark return and benchmark-relative return for each out-of-sample fold. This makes it possible to distinguish strategy improvement from simply owning an asset during a favorable period.

## Walk-forward

The framework uses rolling windows:

```text
train period → choose parameters
subsequent test period → evaluate chosen parameters
advance by step period → repeat
```

The OOS result should be evaluated as a distribution across folds, not only by the best fold. Parameter choice must use training data only; later test data must not influence selection.

## Parameter search

The example walk-forward optimizer scores training candidates using a simple return/drawdown objective. For serious research, document the full search space and keep the objective fixed before reading test results.

## Factor IC

The framework computes Spearman rank correlation between `signal_strength` and forward returns. IC is supporting diagnostic evidence; it does not replace a realistic execution backtest.
