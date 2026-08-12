# Idea Ingestion

The research pipeline is source-neutral. An idea may originate from a manual observation, video, charting platform, community forum, article, research paper, or another public source. Regardless of origin, the source material is normalized into the same structured research record before any implementation or backtest begins.

```text
manual observation ───────┐
video ─────────────────────┤
charting platform ─────────┤
community forum ───────────┤
article / research paper ──┤
other public source ───────┘
             ↓
      source review
             ↓
    normalized idea.md
             ↓
 duplicate / concept check
             ↓
 deterministic strategy code
             ↓
 backtest / validation / reproducibility
```

## Supported source categories

Use generic source types in research records:

- `manual`
- `video`
- `charting_platform`
- `community_forum`
- `article`
- `research_paper`
- `other_web`

The framework does not require or endorse any particular third-party service.

## Source provenance

Record enough provenance to trace the origin without copying the source material into the repository:

- source type
- source URL or reference, when applicable
- author / publisher, when relevant
- publication date, when known
- retrieval date
- a short researcher-written summary of the original claim

A user's local research record may contain the actual source URL. Public examples and templates intentionally avoid third-party brand names.

## Normalize the idea, not the source content

Do not commit full transcripts, posts, articles, scripts, screenshots, or other third-party material unless you have the right to redistribute them. Prefer a researcher-written structured interpretation.

For every source, separate:

1. **Original claim** — what the source appears to assert.
2. **Research thesis** — the market behavior worth testing.
3. **Exact testable interpretation** — deterministic conditions that can be coded.
4. **Ambiguities** — words or rules that required interpretation.
5. **Potential bias** — repainting, look-ahead, survivorship, selection, or execution assumptions that may affect the claim.

## Video-derived ideas

For a video-derived idea:

1. record provenance,
2. obtain notes or a transcript only through a method you are permitted to use,
3. extract entry, exit, filter, regime, and risk concepts,
4. identify subjective language such as "strong", "clean", or "near support",
5. declare a precise testable interpretation,
6. review the interpretation before coding it.

The repository should preserve the interpretation, not a copied transcript.

## Charting-platform ideas

A charting-platform idea may originate from a published description or user-supplied strategy/indicator code. Treat it as a source specification, not as proof.

Before implementing it independently, review potential differences in:

- repainting behavior
- higher-timeframe data alignment
- look-ahead settings
- intrabar calculations
- session and timezone definitions
- order timing
- stop / limit fill assumptions

Automatic source-language-to-Python translation is not part of the v0.1 core workflow.

## Community-forum ideas

Treat a forum post as a hypothesis source, not a validated strategy. Convert the claim into a falsifiable statement and define what evidence would reject it.

For example, a qualitative claim about volatility expansion should become explicit measurements, thresholds, lookback windows, and forward-return horizons before testing.

## Optional automation

An optional local or AI-assisted helper may help normalize researcher-supplied notes into the standard idea template. The normalized result still requires human review before it is bound to deterministic strategy code.

No source-ingestion service is required by the core backtest and validation pipeline.
