import pandas as pd

from fx_research.combination import combine_signal_frames
from fx_research.concepts import jaccard_similarity


def test_jaccard_similarity_prefers_related_text():
    a = "moving average trend crossover"
    assert jaccard_similarity(a, "fast moving average crossover strategy") > jaccard_similarity(a, "liquidity sweep reversal")


def test_combination_union():
    idx = pd.date_range("2025-01-01", periods=3, freq="15min")
    a = pd.DataFrame({"entry": [True, False, False], "signal_strength": [1, 0, 0]}, index=idx)
    b = pd.DataFrame({"entry": [False, True, False], "signal_strength": [0, 2, 0]}, index=idx)
    out = combine_signal_frames([a, b], "union")
    assert out["entry"].tolist() == [True, True, False]
