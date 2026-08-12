from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

STOP = {"the", "and", "or", "a", "an", "to", "of", "in", "on", "for", "with", "is", "be", "when"}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if len(w) > 2 and w not in STOP}


def jaccard_similarity(a: str, b: str) -> float:
    x, y = _tokens(a), _tokens(b)
    if not x or not y:
        return 0.0
    return len(x & y) / len(x | y)


def check_idea(idea_path: str | Path, catalog_path: str | Path) -> pd.DataFrame:
    idea = Path(idea_path).read_text(encoding="utf-8")
    catalog = pd.read_csv(catalog_path).fillna("")
    required = {"name", "description", "status"}
    missing = required - set(catalog.columns)
    if missing:
        raise ValueError(f"Concept catalog missing columns: {sorted(missing)}")
    rows = []
    for _, row in catalog.iterrows():
        comparison = f"{row['name']} {row['description']}"
        rows.append({
            "name": row["name"],
            "status": row["status"],
            "similarity": jaccard_similarity(idea, comparison),
            "notes": row.get("notes", ""),
        })
    return pd.DataFrame(rows).sort_values("similarity", ascending=False).reset_index(drop=True)
