# Reproducibility Standard

Every reported result should identify at least:

| Field | Requirement |
|---|---|
| Strategy source | module/file plus source snapshot |
| Version-control commit | exact commit when available |
| Idea provenance | source type/reference and researcher interpretation |
| Data path/source | where the data came from |
| Data SHA-256 | exact file identity |
| Timezone | declared timestamp timezone |
| Date range | first and last evaluated timestamp |
| Signal timeframe | e.g. M15 |
| Parameters | exact resolved values |
| Starting equity | exact value |
| Risk model | exact sizing rule |
| Costs | spread/commission/slippage assumptions |
| Entry timing | signal bar vs next bar |
| Intrabar ambiguity | stated stop/target precedence |
| Trades | sample size |
| Win rate | outcome frequency |
| Profit factor | payoff quality |
| Total return / CAGR | return metrics |
| Realized max DD | closed-equity risk |
| Floating max DD | mark-to-market risk |
| Benchmark | same-period underlying return |
| Walk-forward | window design, OOS results, and per-fold benchmark |
| Factor IC | horizons and rank correlations |
| Python/packages | environment versions |
| Reproduction command | exact command |

The pipeline writes these fields across `reproducibility_report.md`, `data_manifest.json`, `config.resolved.yaml`, `strategy_source.py`, and the result CSV/JSON files.

Historical comments inside strategy files are research notes, not authoritative performance evidence.
