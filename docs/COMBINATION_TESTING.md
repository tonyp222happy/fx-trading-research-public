# Combination Testing

When a new signal is proposed, do not evaluate only the combined strategy. Preserve separate evidence for:

1. Current baseline alone.
2. New candidate alone.
3. Union / combined signals.
4. A predeclared quality subset if one exists.
5. Best single concept alone.

This five-scenario sequence is a **research protocol**, not a single automated command in v0.1. Each scenario should be represented by a deterministic strategy/configuration and preserved as a separate result.

Report signal overlap and drawdown changes. Combining individually acceptable signals can still create correlated exposure and worse portfolio-level drawdown.

The helper `fx_research.combination.combine_signal_frames()` currently supports transparent `union` and `intersection` combinations. More complex weighting or scenario orchestration should be implemented as deterministic strategy/configuration code so it remains inspectable and reproducible.
