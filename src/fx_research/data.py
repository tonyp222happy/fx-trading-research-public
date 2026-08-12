from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

REQUIRED = {"open", "high", "low", "close"}


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_ohlcv_csv(path: str | Path, datetime_column: str = "datetime", timezone: str | None = None) -> pd.DataFrame:
    path = Path(path)
    df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    dt_col = datetime_column.strip().lower()
    if dt_col not in df.columns:
        raise ValueError(f"Missing datetime column: {datetime_column}")
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    parsed = pd.to_datetime(df[dt_col], errors="raise")
    idx = pd.DatetimeIndex(parsed)
    if timezone:
        try:
            if idx.tz is None:
                idx = idx.tz_localize(timezone, ambiguous="raise", nonexistent="raise")
            else:
                idx = idx.tz_convert(timezone)
        except Exception as exc:
            raise ValueError(f"Could not apply declared timezone {timezone!r}: {exc}") from exc
    df[dt_col] = idx
    df = df.set_index(dt_col).sort_index()
    if df.index.has_duplicates:
        dupes = int(df.index.duplicated().sum())
        raise ValueError(f"Duplicate timestamps found: {dupes}")

    cols = ["open", "high", "low", "close"] + (["volume"] if "volume" in df.columns else [])
    df = df[cols].astype(float)
    if df[cols].isna().any().any():
        raise ValueError("NaN values found in OHLC(V) columns")
    if (df[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("OHLC prices must be positive")
    if (df["high"] < df[["open", "close", "low"]].max(axis=1)).any():
        raise ValueError("Found rows where high is below another OHLC value")
    if (df["low"] > df[["open", "close", "high"]].min(axis=1)).any():
        raise ValueError("Found rows where low is above another OHLC value")
    return df


def resample_ohlcv(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if "volume" in df.columns:
        agg["volume"] = "sum"
    return df.resample(timeframe).agg(agg).dropna(subset=["open", "high", "low", "close"])
