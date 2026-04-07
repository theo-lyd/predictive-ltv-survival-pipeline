"""Automated remediation workflows for Batch 5."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

try:
    from airflow.models import Variable
except ModuleNotFoundError:

    class Variable:  # type: ignore[override]
        """Fallback Variable shim for non-Airflow test environments."""

        @staticmethod
        def get(_key: str, default_var: Any = None):
            return default_var


from config.phase_4_batch_5_observability_config import (
    REMEDIATION_CONFIG,
    RUNBOOK_CONFIG,
)


logger = logging.getLogger(__name__)


def _incident_type(incident: dict[str, Any]) -> str:
    return str(incident.get("type", "UNKNOWN")).upper()


def _incident_severity(incident: dict[str, Any]) -> str:
    return str(incident.get("severity", "MEDIUM")).upper()


def _build_recommendation(incident: dict[str, Any], layer: str) -> dict[str, str]:
    incident_type = _incident_type(incident)
    runbook = RUNBOOK_CONFIG["layer_runbooks"].get(layer, RUNBOOK_CONFIG["default_runbook_url"])
    playbook = RUNBOOK_CONFIG["default_playbook_url"]

    if incident_type == "FRESHNESS":
        action = "re-run ingestion and validate upstream source latency"
    elif incident_type == "VOLUME":
        action = "validate source extraction counts and deduplication filters"
    elif incident_type == "SCHEMA":
        action = "pause downstream model publishing and review schema contract"
    else:
        action = "triage incident manually and assign an owner"

    return {
        "action": action,
        "runbook": runbook,
        "playbook": playbook,
    }


def run_automated_remediation(**context) -> dict[str, Any]:
    """Apply configured remediation actions for incidents captured in MC health tasks."""
    ti = context["task_instance"]

    layer_health = {
        "bronze": ti.xcom_pull(task_ids="mc_check_bronze_health", key="mc_health_bronze") or {},
        "silver": ti.xcom_pull(task_ids="mc_check_silver_health", key="mc_health_silver") or {},
        "gold": ti.xcom_pull(task_ids="mc_check_gold_health", key="mc_health_gold") or {},
    }

    incidents: list[tuple[str, dict[str, Any]]] = []
    for layer, health in layer_health.items():
        for table_data in (health.get("tables") or {}).values():
            for incident in table_data.get("incidents", []):
                incidents.append((layer, incident))

    incidents = incidents[: REMEDIATION_CONFIG["max_incidents_per_run"]]
    hook = None
    if incidents:
        from hooks.monte_carlo_hook import MonteCarloHook

        hook = MonteCarloHook()

    resolved = []
    recommendations = []
    escalations = []

    for layer, incident in incidents:
        incident_id = incident.get("id")
        if not incident_id:
            continue

        severity = _incident_severity(incident)
        incident_type = _incident_type(incident)
        action = REMEDIATION_CONFIG["severity_actions"].get(severity, "recommend_and_notify")

        if incident_type not in REMEDIATION_CONFIG["supported_incident_types"]:
            recommendations.append(
                {
                    "incident_id": incident_id,
                    "layer": layer,
                    "reason": "unsupported_incident_type",
                }
            )
            continue

        if action == "auto_resolve" and REMEDIATION_CONFIG["enable_auto_resolve_low_severity"]:
            note = (
                "Auto-resolved low severity incident during Batch 5 remediation run at "
                f"{datetime.utcnow().isoformat()}"
            )
            try:
                resolution = hook.resolve_incident(incident_id=incident_id, resolution_note=note)
                resolved.append(
                    {"incident_id": incident_id, "resolution": resolution, "layer": layer}
                )
            except Exception as exc:
                recommendations.append(
                    {
                        "incident_id": incident_id,
                        "layer": layer,
                        "reason": f"resolve_failed: {exc}",
                    }
                )
        elif action in {"escalate_and_recommend", "escalate_immediately"}:
            escalations.append({"incident_id": incident_id, "layer": layer, "severity": severity})
            recommendations.append(
                {
                    "incident_id": incident_id,
                    "layer": layer,
                    **_build_recommendation(incident, layer),
                }
            )
        else:
            recommendations.append(
                {
                    "incident_id": incident_id,
                    "layer": layer,
                    **_build_recommendation(incident, layer),
                }
            )

    result = {
        "processed_incidents": len(incidents),
        "resolved_count": len(resolved),
        "recommendation_count": len(recommendations),
        "escalation_count": len(escalations),
        "resolved": resolved,
        "recommendations": recommendations,
        "escalations": escalations,
    }

    owner = Variable.get("LTV_PIPELINE_OWNER", default_var="analytics-engineering")
    logger.info("Automated remediation complete for owner=%s: %s", owner, result)
    ti.xcom_push(key="batch_5_remediation_result", value=result)
    return result
