#!/usr/bin/env python3
"""Build one encrypted annual USA500 M5 shard from Dukascopy M1 candles.

Public-worker safety design:
- HTTPS-only source retrieval from Dukascopy.
- Plaintext exists only on the ephemeral GitHub runner.
- Output artifact contains AES-encrypted tarball plus RSA-OAEP-wrapped password.
- Native Dukascopy M1 candles are all retained before deterministic M5 aggregation.
  Flat/stale zero-volume filtering is intentionally deferred to the private final
  continuous merge so cross-day and cross-shard price continuity is available.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import json
import lzma
import math
import os
import shutil
import struct
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

BASE = "https://datafeed.dukascopy.com/datafeed"
SYMBOL = "USA500IDXUSD"
PRICE_MULTIPLIER = 1000.0
REC = struct.Struct(">iiiiif")
UA = "Mozilla/5.0 aiwen-usa500-public-worker/1.0"
GLOBAL_START = dt.date(2011, 9, 18)
GLOBAL_END = dt.date(2024, 10, 22)
TRANSIENT_HTTP = {429, 500, 502, 503, 504}


@dataclass
class DayResult:
    day: dt.date
    status: str
    rows: list[list[object]]
    source_rows: int = 0
    zero_source_rows: int = 0
    partial_m5: int = 0
    error: str | None = None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt_epoch(sec: int) -> str:
    return (
        dt.datetime.fromtimestamp(sec, tz=dt.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def validate_ohlc(o: float, h: float, l: float, c: float) -> None:
    vals = (o, h, l, c)
    if any((not math.isfinite(v)) or v <= 0 for v in vals):
        raise ValueError(f"non-finite/non-positive OHLC: {vals}")
    if h < max(o, c) or l > min(o, c) or h < l:
        raise ValueError(f"invalid OHLC geometry: {vals}")


def source_url(day: dt.date) -> str:
    return (
        f"{BASE}/{SYMBOL}/{day.year:04d}/{day.month - 1:02d}/"
        f"{day.day:02d}/BID_candles_min_1.bi5"
    )


def fetch_bytes(day: dt.date, *, recovery: bool = False) -> tuple[str, bytes | None, str | None]:
    attempts = 8 if recovery else 5
    timeout = 60 if recovery else 30
    last: str | None = None
    url = source_url(day)
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read()
            if not raw:
                return "not_found", None, None
            return "data", raw, None
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return "not_found", None, None
            last = f"HTTP {exc.code}"
            if exc.code not in TRANSIENT_HTTP:
                break
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = repr(exc)
        if attempt < attempts:
            cap = 20 if recovery else 8
            time.sleep(min(0.5 * (1.7 ** attempt), cap))
    return "error", None, last or "unknown fetch error"


def resample_payload(day: dt.date, raw: bytes) -> DayResult:
    try:
        payload = lzma.decompress(raw)
    except Exception as exc:
        return DayResult(day, "error", [], error=f"LZMA: {exc}")
    if len(payload) % REC.size:
        return DayResult(
            day, "error", [], error=f"payload {len(payload)} not divisible by {REC.size}"
        )

    day_start = int(dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp())
    rows: list[list[object]] = []
    bucket: int | None = None
    bo = bh = bl = bc = None
    volume = 0.0
    source_minutes = 0
    zero_minutes = 0
    source_rows = 0
    zero_source_rows = 0
    prior_off: int | None = None

    def flush() -> None:
        nonlocal bucket, bo, bh, bl, bc, volume, source_minutes, zero_minutes
        if bucket is None:
            return
        if bo is None or bh is None or bl is None or bc is None:
            raise RuntimeError("empty M5 bucket")
        rows.append([
            fmt_epoch(bucket), bo, bh, bl, bc, volume, source_minutes, zero_minutes
        ])
        bucket = None
        bo = bh = bl = bc = None
        volume = 0.0
        source_minutes = 0
        zero_minutes = 0

    for offset in range(0, len(payload), REC.size):
        sec_off, o_raw, c_raw, l_raw, h_raw, vol_raw = REC.unpack_from(payload, offset)
        if sec_off < 0 or sec_off >= 86400 or sec_off % 60 != 0:
            return DayResult(day, "error", [], error=f"invalid minute offset {sec_off}")
        if prior_off is not None and sec_off <= prior_off:
            return DayResult(day, "error", [], error=f"non-increasing offsets {prior_off}->{sec_off}")
        prior_off = sec_off

        o = o_raw / PRICE_MULTIPLIER
        c = c_raw / PRICE_MULTIPLIER
        l = l_raw / PRICE_MULTIPLIER
        h = h_raw / PRICE_MULTIPLIER
        v = float(vol_raw)
        try:
            validate_ohlc(o, h, l, c)
        except Exception as exc:
            return DayResult(day, "error", [], error=str(exc))
        if not math.isfinite(v) or v < 0:
            return DayResult(day, "error", [], error=f"invalid volume {v}")

        ts = day_start + sec_off
        b = ts - (ts % 300)
        if bucket is not None and b != bucket:
            flush()
        if bucket is None:
            bucket = b
            bo = o
            bh = h
            bl = l
        else:
            bh = max(float(bh), h)
            bl = min(float(bl), l)
        bc = c
        volume += v
        source_minutes += 1
        source_rows += 1
        if v == 0.0:
            zero_minutes += 1
            zero_source_rows += 1

    flush()
    partial = sum(int(r[6]) != 5 for r in rows)
    return DayResult(
        day,
        "data" if source_rows else "not_found",
        rows,
        source_rows=source_rows,
        zero_source_rows=zero_source_rows,
        partial_m5=partial,
    )


def fetch_day(day: dt.date, *, recovery: bool = False) -> DayResult:
    status, raw, error = fetch_bytes(day, recovery=recovery)
    if status != "data":
        return DayResult(day, status, [], error=error)
    assert raw is not None
    return resample_payload(day, raw)


def date_range(year: int) -> list[dt.date]:
    start = max(GLOBAL_START, dt.date(year, 1, 1))
    end = min(GLOBAL_END, dt.date(year, 12, 31))
    if start > end:
        return []
    out: list[dt.date] = []
    cur = start
    while cur <= end:
        out.append(cur)
        cur += dt.timedelta(days=1)
    return out


def build_year(year: int, workers: int, plain_dir: Path) -> tuple[Path, Path, dict[str, object]]:
    days = date_range(year)
    if not days:
        raise RuntimeError(f"empty year range {year}")
    print(f"USA500 {year}: {days[0]} -> {days[-1]}, {len(days)} days, workers={workers}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(fetch_day, days))

    failed = [r for r in results if r.status == "error"]
    if failed:
        print(f"USA500 {year}: recovery pass for {len(failed)} failed days", flush=True)
        by_day = {r.day: r for r in results}
        for old in failed:
            by_day[old.day] = fetch_day(old.day, recovery=True)
        results = [by_day[d] for d in days]

    unresolved = [
        {"day": r.day.isoformat(), "error": r.error or "unknown"}
        for r in results if r.status == "error"
    ]
    if unresolved:
        raise RuntimeError("unresolved fetch failures: " + json.dumps(unresolved))

    csv_path = plain_dir / f"USA500IDXUSD_DUKASCOPY_BID_M5_RAW_{year}.csv.gz"
    meta_path = plain_dir / f"USA500IDXUSD_DUKASCOPY_BID_M5_RAW_{year}.json"
    source_rows = zero_source_rows = m5_rows = partial = 0
    data_days = not_found_days = 0
    first_ts = last_ts = None
    prior_epoch: int | None = None

    with gzip.open(csv_path, "wt", encoding="utf-8", newline="", compresslevel=9) as handle:
        w = csv.writer(handle)
        w.writerow([
            "timestamp", "open", "high", "low", "close", "volume",
            "source_minutes", "zero_volume_minutes"
        ])
        for r in results:
            if r.status == "not_found":
                not_found_days += 1
                continue
            data_days += 1
            source_rows += r.source_rows
            zero_source_rows += r.zero_source_rows
            partial += r.partial_m5
            for row in r.rows:
                ts = str(row[0])
                epoch = int(dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
                if prior_epoch is not None and epoch <= prior_epoch:
                    raise RuntimeError(f"non-increasing output at {ts}")
                prior_epoch = epoch
                w.writerow(row)
                m5_rows += 1
                if first_ts is None:
                    first_ts = ts
                last_ts = ts

    if m5_rows < 1000 or first_ts is None or last_ts is None:
        raise RuntimeError(f"year {year} unexpectedly small: {m5_rows}")

    meta: dict[str, object] = {
        "schema": "aiwen_usa500_dukascopy_raw_year_v1",
        "year": year,
        "requested_start": days[0].isoformat(),
        "requested_end": days[-1].isoformat(),
        "source": "Dukascopy direct DataFeed BID M1",
        "source_url_pattern": (
            "https://datafeed.dukascopy.com/datafeed/USA500IDXUSD/"
            "YYYY/MM0/DD/BID_candles_min_1.bi5"
        ),
        "source_transport": "HTTPS only",
        "source_m1_rows": source_rows,
        "zero_volume_source_minutes": zero_source_rows,
        "m5_rows_raw": m5_rows,
        "partial_m5_rows": partial,
        "days_with_source_file": data_days,
        "days_not_found": not_found_days,
        "first_output_timestamp": first_ts,
        "last_output_timestamp": last_ts,
        "stale_fill_policy": (
            "No M1 rows are discarded in the public worker. Flat/stale filtering "
            "is deferred to the private continuous merge."
        ),
        "csv_file": csv_path.name,
        "csv_sha256": sha256(csv_path),
        "csv_size_bytes": csv_path.stat().st_size,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return csv_path, meta_path, meta


def encrypt_bundle(year: int, plain_dir: Path, out_dir: Path, public_key: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    tar_path = plain_dir.parent / f"usa500_{year}_plain.tar.gz"
    members = sorted(plain_dir.iterdir())
    with tarfile.open(tar_path, "w:gz") as tar:
        for member in members:
            tar.add(member, arcname=member.name)

    password_path = plain_dir.parent / "password.txt"
    password_path.write_text(os.urandom(32).hex(), encoding="ascii")
    enc_path = out_dir / f"USA500_DUKASCOPY_M5_RAW_{year}.tar.gz.aes256cbc"
    wrapped_path = out_dir / f"USA500_DUKASCOPY_M5_RAW_{year}.password.rsa_oaep_sha256"

    subprocess.run([
        "openssl", "enc", "-aes-256-cbc", "-salt", "-pbkdf2", "-iter", "200000",
        "-pass", f"file:{password_path}", "-in", str(tar_path), "-out", str(enc_path)
    ], check=True)
    subprocess.run([
        "openssl", "pkeyutl", "-encrypt", "-pubin", "-inkey", str(public_key),
        "-pkeyopt", "rsa_padding_mode:oaep", "-pkeyopt", "rsa_oaep_md:sha256",
        "-in", str(password_path), "-out", str(wrapped_path)
    ], check=True)

    manifest = {
        "schema": "aiwen_encrypted_public_worker_artifact_v1",
        "year": year,
        "cipher": "AES-256-CBC + PBKDF2-SHA256(iter=200000)",
        "password_wrap": "RSA-3072 OAEP SHA-256",
        "plaintext_tar_sha256": sha256(tar_path),
        "encrypted_file": enc_path.name,
        "encrypted_sha256": sha256(enc_path),
        "encrypted_size_bytes": enc_path.stat().st_size,
        "wrapped_password_file": wrapped_path.name,
        "wrapped_password_sha256": sha256(wrapped_path),
    }
    (out_dir / f"USA500_DUKASCOPY_M5_RAW_{year}.encryption.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    password_path.unlink(missing_ok=True)
    tar_path.unlink(missing_ok=True)
    shutil.rmtree(plain_dir, ignore_errors=True)
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--public-key", type=Path, required=True)
    args = ap.parse_args()
    if not 2011 <= args.year <= 2024:
        raise SystemExit("year must be 2011..2024")
    if not 1 <= args.workers <= 8:
        raise SystemExit("workers must be 1..8")
    if not args.public_key.is_file():
        raise SystemExit("public key not found")

    with tempfile.TemporaryDirectory(prefix=f"usa500-{args.year}-") as temp:
        root = Path(temp)
        plain = root / "plain"
        plain.mkdir()
        _, _, meta = build_year(args.year, args.workers, plain)
        manifest = encrypt_bundle(args.year, plain, args.output_dir, args.public_key)
        print(json.dumps({"dataset": meta, "encryption": manifest}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
