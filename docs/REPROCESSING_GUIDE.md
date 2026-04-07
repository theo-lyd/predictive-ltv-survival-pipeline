# Reprocessing Guide

This guide describes how to rebuild the Phase 7 monitoring outputs after a data refresh, incident, or recovery action.

## When to Reprocess

Reprocess when:
- the SLA report changed after a data reload,
- the operational snapshot is stale,
- a compliance audit artifact needs regeneration,
- an incident requires a fresh evidence bundle.

## Standard Reprocess Sequence

1. Rebuild the SLA monitor outputs:

```bash
python scripts/monitor_sla_compliance.py \
  --output logs/sla_report.json \
  --history-file logs/sla_history.jsonl \
  --audit-output logs/compliance_audit.json
```

2. Rebuild the operational snapshot:

```bash
python scripts/export_operational_snapshot.py \
  --output logs/operational_snapshot.json \
  --history-file logs/sla_history.jsonl
```

3. Rebuild the compliance audit bundle:

```bash
python scripts/export_compliance_audit.py \
  --output logs/compliance_audit.json \
  --report-file logs/sla_report.json \
  --history-file logs/sla_history.jsonl
```

4. Validate latency and cache behavior:

```bash
make phase7-latency
```

## If History Needs to Be Recreated

If the history file is missing, the monitor recreates it from the current report when possible. That keeps the dashboard and audit exports aligned on the same source of truth.

If you need a completely clean history:
1. Remove the existing local history file.
2. Run the monitor again to seed fresh rows.
3. Rebuild the snapshot and audit bundle.

## Rerun, Rollback, and Reprocess Rules

- Rerun: use the same commands when a transient issue was resolved.
- Rollback: revert the upstream data or report change before re-running.
- Reprocess: regenerate all three artifacts after any material data refresh.

## Output Artifacts

Expected artifacts after a reprocess:
- `logs/sla_report.json`
- `logs/sla_history.jsonl`
- `logs/operational_snapshot.json`
- `logs/compliance_audit.json`

## Recommended Operator Behavior

1. Reprocess immediately after fixing the upstream issue.
2. Confirm the new report grade and history count.
3. Attach the audit artifact to the incident or review record.
4. Keep the previous artifact only if it is needed for postmortem comparison.
