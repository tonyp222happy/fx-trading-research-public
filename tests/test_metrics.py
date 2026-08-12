import pandas as pd

from fx_research.metrics import max_drawdown


def test_max_drawdown():
    s = pd.Series([100, 120, 90, 108])
    assert round(max_drawdown(s), 4) == -0.25
