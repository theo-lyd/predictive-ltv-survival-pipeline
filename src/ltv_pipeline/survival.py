"""Survival analysis helpers for the thesis scaffold."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SurvivalCurveResult:
    cohort_name: str
    summary: pd.DataFrame


def build_kaplan_meier_summary(
    frame: pd.DataFrame, duration_col: str, event_col: str, cohort_name: str
) -> SurvivalCurveResult:
    """Return a lightweight survival summary placeholder.

    The full Kaplan-Meier implementation can be swapped in later using lifelines.
    """

    summary = frame[[duration_col, event_col]].copy()
    summary = summary.sort_values(duration_col).reset_index(drop=True)
    summary["survival_step"] = 1.0 - (summary[event_col].cumsum() / max(len(summary), 1))
    return SurvivalCurveResult(cohort_name=cohort_name, summary=summary)
