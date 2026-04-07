# Compliance Audit Process

This guide defines how to generate, review, and archive compliance artifacts introduced in Phase 7 Batch 3.

## Purpose

The process ensures SLA and governance evidence is generated from the platform itself and can be reviewed without reconstructing events manually.

## Daily Operational Flow

1. Run monitor and emit report, history, and audit artifact:

```bash
python scripts/monitor_sla_compliance.py \
  --output logs/sla_report.json \
  --history-file logs/sla_history.jsonl \
  --audit-output logs/compliance_audit.json
```

2. Confirm generated files:
- `logs/sla_report.json`
- `logs/sla_history.jsonl`
- `logs/compliance_audit.json`

3. Validate artifact integrity:
- `artifact_type == sla_compliance_audit`
- `schema_version` present
- `history.run_count >= 1`

## Weekly Governance Review

1. Export an explicit review artifact from current report/history:

```bash
python scripts/export_compliance_audit.py \
  --output logs/compliance_audit_weekly.json \
  --report-file logs/sla_report.json \
  --history-file logs/sla_history.jsonl
```

2. Review sections in order:
- `summary` for current posture
- `history.trend_summary` for direction of risk
- `evidence.records` for action traceability

3. Capture decisions:
- accepted risks,
- required remediations,
- due dates and owners.

## Incident/Postmortem Usage

For every SLA incident:
1. Attach the latest compliance artifact to incident notes.
2. Include top breach evidence records (`evidence.records`).
3. Record run-over-run movement using:
- `history.trend_summary.score_delta`
- `history.trend_summary.breach_delta`
4. Store final artifact with incident timeline assets.

## Retention and Traceability

Recommended retention:
- Daily artifacts: 30 days
- Weekly governance artifacts: 90 days
- Monthly sign-off artifacts: 12 months

Minimum traceability fields for each review:
- artifact file path
- generated timestamp
- reviewer
- sign-off outcome
- remediation references
