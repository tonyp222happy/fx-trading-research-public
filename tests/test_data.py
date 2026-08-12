import pandas as pd
import pytest

from fx_research.data import load_ohlcv_csv, resample_ohlcv


def test_load_and_resample(tmp_path):
    p = tmp_path / "x.csv"
    pd.DataFrame({
        "datetime": pd.date_range("2025-01-01", periods=6, freq="5min"),
        "open": [1,1,1,1,1,1], "high": [1.1]*6, "low": [0.9]*6, "close": [1.0]*6
    }).to_csv(p, index=False)
    df = load_ohlcv_csv(p)
    m15 = resample_ohlcv(df, "15min")
    assert len(m15) == 2


def test_duplicate_timestamp_rejected(tmp_path):
    p = tmp_path / "x.csv"
    pd.DataFrame({
        "datetime": ["2025-01-01", "2025-01-01"],
        "open": [1,1], "high": [1.1,1.1], "low": [0.9,0.9], "close": [1,1]
    }).to_csv(p, index=False)
    with pytest.raises(ValueError, match="Duplicate"):
        load_ohlcv_csv(p)


def test_declared_timezone_localizes_naive_timestamps(tmp_path):
    p = tmp_path / "tz.csv"
    pd.DataFrame({
        "datetime": pd.date_range("2025-01-01", periods=3, freq="5min"),
        "open": [1,1,1], "high": [1.1]*3, "low": [0.9]*3, "close": [1.0]*3
    }).to_csv(p, index=False)
    df = load_ohlcv_csv(p, timezone="UTC")
    assert str(df.index.tz) == "UTC"
