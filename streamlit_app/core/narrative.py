"""Narrative helpers for AI-supported storytelling."""

from __future__ import annotations

import json
from pathlib import Path


ARTIFACT_PATH = Path(__file__).resolve().parents[2] / "airflow" / "artifacts" / "executive_storytelling" / "daily_summary.json"

REQUIRED_NARRATIVE_KEYS = {
    "summary_date": str,
    "headline": str,
    "insights": list,
    "actions": list,
    "provenance": str,
}


def narrative_snapshot_timestamp() -> float:
    """Timestamp key for Streamlit cache invalidation of narrative artifact."""
    if ARTIFACT_PATH.exists():
        return ARTIFACT_PATH.stat().st_mtime
    return 0.0


def validate_narrative_contract(payload: dict) -> tuple[bool, list[str]]:
    """Lightweight schema contract check for narrative artifact before render."""
    errors: list[str] = []
    for key, expected_type in REQUIRED_NARRATIVE_KEYS.items():
        if key not in payload:
            errors.append(f"missing:{key}")
            continue
        if not isinstance(payload[key], expected_type):
            errors.append(f"type:{key}:{expected_type.__name__}")

    if "insights" in payload and isinstance(payload.get("insights"), list):
        if any(not isinstance(item, str) for item in payload["insights"]):
            errors.append("type:insights:item:str")
    if "actions" in payload and isinstance(payload.get("actions"), list):
        if any(not isinstance(item, str) for item in payload["actions"]):
            errors.append("type:actions:item:str")

    return len(errors) == 0, errors


def _fallback_summary(contract_errors: list[str] | None = None) -> dict:
    return {
        "summary_date": None,
        "headline": "AI summary not generated yet.",
        "insights": [
            "Run the daily summary workflow in Airflow to produce grounded narrative deltas.",
        ],
        "actions": ["Validate that Gold-layer metrics are up to date before stakeholder review."],
        "provenance": "fallback-template",
        "contract_valid": False if contract_errors else True,
        "contract_errors": contract_errors or [],
    }


def load_daily_summary() -> dict:
    if ARTIFACT_PATH.exists():
        try:
            payload = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return _fallback_summary(contract_errors=["invalid_json"])

        is_valid, errors = validate_narrative_contract(payload)
        if not is_valid:
            return _fallback_summary(contract_errors=errors)

        payload["contract_valid"] = True
        payload["contract_errors"] = []
        return payload

    return _fallback_summary()
