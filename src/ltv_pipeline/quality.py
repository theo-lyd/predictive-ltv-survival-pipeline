"""Quality and validation helpers for the scaffold."""

from __future__ import annotations

import pandas as pd


def validate_invoice_math(
    frame: pd.DataFrame, original_col: str, discount_col: str, final_col: str
) -> pd.Series:
    """Return a boolean mask showing whether invoice math is valid."""

    expected = frame[original_col] - frame[discount_col]
    return expected.round(2) == frame[final_col].round(2)
