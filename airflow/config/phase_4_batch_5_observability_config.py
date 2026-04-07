"""Batch 5 configuration for observability dashboards, runbooks, remediation, and anomaly learning."""

from datetime import timedelta

# Dashboard publication targets
DASHBOARD_CONFIG = {
    "grafana": {
        "enabled": True,
        "output_path": "airflow/artifacts/grafana/ltv_pipeline_dashboard.json",
        "dashboard_uid": "ltv-survival-pipeline",
        "dashboard_title": "LTV Survival Pipeline - Data Quality",
    },
    "datadog": {
        "enabled": True,
        "api_host": "https://api.datadoghq.com/api/v1/series",
        "metric_namespace": "ltv_pipeline",
    },
}

# Incident runbook and playbook references
RUNBOOK_CONFIG = {
    "default_runbook_url": "docs/PHASE_4_BATCH_5_INCIDENT_RUNBOOKS.md",
    "default_playbook_url": "docs/PHASE_4_BATCH_5_INCIDENT_PLAYBOOKS.md",
    "layer_runbooks": {
        "bronze": "docs/PHASE_4_BATCH_5_INCIDENT_RUNBOOKS.md#bronze-layer-runbook",
        "silver": "docs/PHASE_4_BATCH_5_INCIDENT_RUNBOOKS.md#silver-layer-runbook",
        "gold": "docs/PHASE_4_BATCH_5_INCIDENT_RUNBOOKS.md#gold-layer-runbook",
    },
}

# Automated remediation controls
REMEDIATION_CONFIG = {
    "enable_auto_resolve_low_severity": True,
    "enable_retry_failed_monitors": True,
    "max_incidents_per_run": 20,
    "supported_incident_types": ["VOLUME", "FRESHNESS", "SCHEMA"],
    "severity_actions": {
        "LOW": "auto_resolve",
        "MEDIUM": "recommend_and_notify",
        "HIGH": "escalate_and_recommend",
        "CRITICAL": "escalate_immediately",
    },
    "cooldown_period": timedelta(minutes=30),
}

# Advanced anomaly learning
ANOMALY_LEARNING_CONFIG = {
    "enabled": True,
    "lookback_days": 30,
    "min_points": 10,
    "zscore_threshold": 2.5,
    "max_monitors_per_run": 50,
    "learning_output_path": "airflow/artifacts/anomaly-learning/monitor-thresholds.json",
}

# DAG behavior for observability phase
BATCH_5_DAG_CONFIG = {
    "fail_pipeline_on_observability_errors": False,
    "emit_dashboard_artifacts": True,
    "emit_datadog_metrics": True,
    "run_automated_remediation": True,
    "run_anomaly_learning": True,
}
