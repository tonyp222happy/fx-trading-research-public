# Example Strategy Idea — MA Trend Crossover

## Purpose
A deliberately simple educational hypothesis used to demonstrate the public research workflow. It is not a production strategy.

## Environment
- Input: OHLC(V) data
- Signal timeframe: M15
- Direction: long only

## State
- Fast moving average of close
- Slow moving average of close

## Entry hypothesis
Enter after the fast moving average crosses above the slow moving average on a closed bar.

## Exit / risk rules
The generic backtest engine applies a fixed percentage stop, fixed percentage target, and maximum holding period from YAML configuration.

## Factor hypothesis
The normalized distance between the fast and slow averages is used only as an example `signal_strength` factor for IC analysis.

## Research warning
No claim is made that this strategy has economic value. The included sample data is synthetic.
