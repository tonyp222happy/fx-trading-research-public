# Research Process

The public workflow ends at documented reproducibility.

## 1. Idea discovery
Record the origin of the hypothesis. Discovery may be manual or may begin from a video, charting platform, community forum, article, research paper, or another source. Normalize every source into the same structured idea record before implementation. Do not commit third-party material you do not have rights to redistribute. See [IDEA_INGESTION.md](IDEA_INGESTION.md).

## 2. Concept review
Write the idea in a structured Markdown document. Separate:

- Environment — asset, timeframe, market regime.
- State — information observable at decision time.
- Action — entry, exit, or filter behavior.
- Risk rules — rules that depend on entry price or current position state.

## 3. Duplicate / concept check
Compare the hypothesis with previously tested concepts. Redundant or previously rejected ideas should be documented rather than silently retested.

## 4. Deterministic Python implementation
Translate the idea into closed-bar code. Natural-language descriptions are not backtests. The implementation must specify exact conditions and timing.

## 5. Backtest + benchmark
Run the strategy under explicit execution assumptions and compare it with the same-period underlying return.

## 6. Combination / parameter testing
If multiple signals or parameter values are tested, preserve the full search space. Do not report only the best combination.

## 7. Walk-forward validation
Use train/test windows so parameter selection happens only on earlier data and evaluation happens on later unseen data.

## 8. Factor / IC analysis
Where a numeric signal-strength measure exists, test its Spearman rank correlation with forward returns at multiple horizons.

## 9. Documentation + reproducibility
A result can be described as reproducible only when the exact code, data identity, date range, parameters, assumptions, commands, and outputs are recorded.

## Public stop point
Platform-specific trading translation, broker integration, production parity, deployment, and live monitoring are intentionally excluded from this repository.
