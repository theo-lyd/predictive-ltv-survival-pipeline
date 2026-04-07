"""Daily AI-supported summary generation for executive storytelling."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from airflow.models import Variable

from config.phase_5_executive_storytelling_config import EXEC_SUMMARY_CONFIG


logger = logging.getLogger(__name__)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _safe_mkdir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _resolve_output_path(configured_path: str) -> str:
    if os.path.isabs(configured_path):
        return configured_path
    cwd = os.getcwd()
    normalized = configured_path
    if os.path.basename(cwd) == "airflow" and configured_path.startswith("airflow/"):
        normalized = configured_path.split("airflow/", 1)[1]
    return os.path.join(cwd, normalized)


def _load_metric_snapshot() -> dict[str, Any]:
    root = _repo_root()
    churn_path = root / "data" / "raw" / "churn" / "baseline_churn.csv"
    billing_path = root / "data" / "raw" / "billing" / "billing_sync.csv"

    churn = pd.read_csv(churn_path) if churn_path.exists() else pd.DataFrame()
    billing = pd.read_csv(billing_path) if billing_path.exists() else pd.DataFrame()

    if not churn.empty:
        churn["churn_date"] = pd.to_datetime(churn["churn_date"], errors="coerce")
        churn_rate = float(churn["churn_date"].notna().mean())
    else:
        churn_rate = 0.0

    invoice_count = int(len(billing)) if not billing.empty else 0
    active_customers = int(churn["customer_id"].nunique()) if not churn.empty else 0

    return {
        "churn_rate": churn_rate,
        "invoice_count": invoice_count,
        "active_customers": active_customers,
    }


def _fallback_summary(snapshot: dict[str, Any], obs: dict[str, Any]) -> dict[str, Any]:
    nrr = snapshot.get("summary", {}).get("healthy_layers", 0)
    degraded = snapshot.get("summary", {}).get("degraded_layers", 0)
    headline = (
        f"Pipeline health: {nrr} healthy layer(s), {degraded} degraded layer(s). "
        f"Observed churn rate is {obs['churn_rate'] * 100:.1f}%."
    )

    return {
        "summary_date": datetime.utcnow().date().isoformat(),
        "headline": headline,
        "insights": [
            f"Active customers in snapshot: {obs['active_customers']}",
            f"Billing invoice count in latest extract: {obs['invoice_count']}",
            "Use survival and discount simulator views to test policy changes before rollout.",
        ],
        "actions": [
            "Review degraded layers and assign owner in RevOps standup.",
            "Re-check discount policy if projected NRR uplift is below threshold.",
        ],
        "provenance": "fallback-template",
    }


def _llm_summary(snapshot: dict[str, Any], obs: dict[str, Any]) -> dict[str, Any]:
    api_key = Variable.get("OPENAI_API_KEY", default_var="")
    if not api_key or not EXEC_SUMMARY_CONFIG["use_llm"]:
        return _fallback_summary(snapshot, obs)

    model = Variable.get("OPENAI_MODEL", default_var="gpt-4o-mini")

    prompt = (
        "You are an executive analytics copilot. Create a concise daily business summary from the data. "
        "Return JSON with keys: headline, insights (list of 3), actions (list of 2).\n"
        f"Observability snapshot: {json.dumps(snapshot)[:EXEC_SUMMARY_CONFIG['max_prompt_chars']]}\n"
        f"Business metrics: {json.dumps(obs)}"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You produce grounded business summaries for executives."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=EXEC_SUMMARY_CONFIG["llm_timeout_seconds"],
        )
        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return {
            "summary_date": datetime.utcnow().date().isoformat(),
            "headline": parsed.get("headline", "Daily summary unavailable."),
            "insights": parsed.get("insights", []),
            "actions": parsed.get("actions", []),
            "provenance": f"llm:{model}",
        }
    except Exception as exc:
        logger.warning("LLM summary generation failed; falling back. Error: %s", exc)
        return _fallback_summary(snapshot, obs)


def generate_daily_ai_summary(**context) -> dict[str, Any]:
    """Generate and persist daily executive summary from latest data snapshot."""
    ti = context["task_instance"]
    snapshot = ti.xcom_pull(
        key="batch_5_observability_snapshot",
        task_ids="phase_5_observability.collect_observability_snapshot",
    ) or {}

    obs = _load_metric_snapshot()
    summary = _llm_summary(snapshot, obs)

    output_path = _resolve_output_path(EXEC_SUMMARY_CONFIG["artifact_path"])
    _safe_mkdir(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    ti.xcom_push(key="daily_ai_summary", value=summary)
    logger.info("Daily AI summary generated at %s", output_path)
    return {"status": "generated", "path": output_path, "summary": summary}
