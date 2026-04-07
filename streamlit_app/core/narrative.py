"""Narrative helpers for AI-supported storytelling."""

from __future__ import annotations

import json
from pathlib import Path


ARTIFACT_PATH = Path(__file__).resolve().parents[2] / "airflow" / "artifacts" / "executive_storytelling" / "daily_summary.json"


def load_daily_summary() -> dict:
    if ARTIFACT_PATH.exists():
        return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    return {
        "summary_date": None,
        "headline": "AI summary not generated yet.",
        "insights": [
            "Run the daily summary workflow in Airflow to produce grounded narrative deltas.",
        ],
        "actions": ["Validate that Gold-layer metrics are up to date before stakeholder review."],
        "provenance": "fallback-template",
    }
