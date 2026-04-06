"""Reusable ingestion utilities for Bronze pipeline processing."""

from __future__ import annotations

import re

import pandas as pd


def normalize_numeric_abbrev(value: str | float | int | None) -> float | None:
    """Normalize shorthand numerics such as 1.2K or 3 Mio into raw numbers."""

    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    raw = str(value).strip().replace(",", "")
    if raw == "":
        return None

    match = re.match(r"^([0-9]*\.?[0-9]+)\s*(k|mio|m|million)?$", raw.lower())
    if not match:
        return None

    number = float(match.group(1))
    suffix = match.group(2)
    if suffix == "k":
        return number * 1_000
    if suffix in {"mio", "m", "million"}:
        return number * 1_000_000
    return number
