# Optional AI Layer

AI is not required by the core framework.

A future or user-supplied AI helper may convert researcher-supplied notes derived from a video, charting platform, community forum, article, research paper, or other source into the standard Markdown idea template, or propose a Python adapter. The output must still pass the same deterministic review process:

```text
external source → researcher notes → optional helper → idea.md → human review → deterministic strategy code
```

Never treat generated code as validated merely because it was produced from a natural-language strategy description. Review timing, look-ahead risk, parameter definitions, and execution assumptions before running it.

Do not commit copied third-party transcripts, posts, articles, source code, or other material unless you have the right to redistribute it.

See [IDEA_INGESTION.md](IDEA_INGESTION.md) for the source-neutral ingestion workflow.
