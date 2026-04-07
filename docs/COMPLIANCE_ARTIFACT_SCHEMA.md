# Compliance Artifact Schema

This document defines the JSON structure produced by Batch 3 compliance exports.

## Artifact Overview

Artifact type:
- `sla_compliance_audit`

Current schema version:
- `1.0.0`

Primary producers:
- `scripts/monitor_sla_compliance.py --audit-output ...`
- `scripts/export_compliance_audit.py --output ...`

## Top-Level Fields

Required top-level keys:
- `schema_version` (string)
- `artifact_type` (string)
- `generated_at` (ISO timestamp)
- `summary` (object)
- `history` (object)
- `evidence` (object)

## Summary Section

The `summary` object captures current-state compliance posture:
- `overall_score` (number)
- `grade` (string)
- `source_layer` (string)
- `alert_count` (integer)
- `breach_count` (integer)
- `warning_count` (integer)
- `contract_valid` (boolean)

## History Section

The `history` object captures trend and retention context:
- `row_count` (integer): total JSONL history rows read
- `run_count` (integer): total unique SLA runs derived from history
- `latest_run_at` (ISO timestamp or null)
- `trend_summary` (object)
- `recent_runs` (array): last up to 10 aggregated run records

`trend_summary` includes:
- `score_delta` (number or null)
- `breach_delta` (integer or null)
- `history_freshness_hours` (number or null)

## Evidence Section

The `evidence` object ties alerts to operator-visible context:
- `breaches` (array): raw breach items from current SLA report
- `warnings` (array): raw warning items from current SLA report
- `records` (array): flattened evidence records for audit filtering
- `current_report` (object): full current SLA report snapshot
- `operational_snapshot` (object): run-over-run operational snapshot

Each `records` item includes:
- `layer`, `metric`, `status`, `severity`
- `owner`, `alert_channel`
- `recommended_action`, `evidence`
- `actual`, `target`

## Example Shape

```json
{
  "schema_version": "1.0.0",
  "artifact_type": "sla_compliance_audit",
  "generated_at": "2026-04-07T13:00:00+00:00",
  "summary": {
    "overall_score": 92.5,
    "grade": "B",
    "source_layer": "gold",
    "alert_count": 1,
    "breach_count": 1,
    "warning_count": 1,
    "contract_valid": true
  },
  "history": {
    "row_count": 80,
    "run_count": 20,
    "latest_run_at": "2026-04-07T12:55:00+00:00",
    "trend_summary": {
      "score_delta": -1.5,
      "breach_delta": 1,
      "history_freshness_hours": 0.1
    },
    "recent_runs": []
  },
  "evidence": {
    "breaches": [],
    "warnings": [],
    "records": [],
    "current_report": {},
    "operational_snapshot": {}
  }
}
```
