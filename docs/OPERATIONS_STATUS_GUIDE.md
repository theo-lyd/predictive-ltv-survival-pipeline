# Operations Status Guide

This guide explains how to use the Operations Status view and operational snapshot export to monitor SLA compliance health over time.

## Purpose

The Operations Status page is designed for fast triage and trend review.

Use it to:
- check current SLA health at a glance,
- compare latest run against the previous run,
- identify breach and warning direction before incidents escalate,
- export a machine-readable operational snapshot for external reporting.

## Quick Status Workflow

1. Open the Operations Status page in Streamlit.
2. Verify latest run grade, score, and contract validity.
3. Review breach and warning counters and their delta from previous run.
4. Confirm source layer and alert volume.
5. If breaches increased or grade dropped, start deep review.

## Deep Review Workflow

1. Use the grade trend chart to locate when degradation started.
2. Use breach/warning trend chart to determine if risk is growing.
3. Cross-check with SLA Compliance page details by layer/metric.
4. Validate whether the issue is from contract failures, data quality drift, or freshness gaps.
5. Document findings and route to owners.

## Escalation Guidance

Escalate immediately when any of the following occurs:
- grade drops by one full band (for example A to B or B to C),
- breach count increases compared to previous run,
- contract validity changes from valid to invalid,
- source layer falls back from gold to non-gold unexpectedly,
- alert volume spikes with concurrent score decline.

Suggested escalation channel: on-call data quality incident workflow and stakeholder notification.

## Snapshot Export

Run the export script to generate a JSON snapshot:

```bash
python scripts/export_operational_snapshot.py --output-path artifacts/operational_snapshot.json
```

Optional input flags:
- `--report-path`: path to SLA report JSON (defaults to `artifacts/sla_report.json`)
- `--history-path`: path to SLA history JSONL (defaults to `artifacts/sla_history.jsonl`)

The export output includes:
- latest run metrics and timestamps,
- previous run metrics,
- run-over-run deltas,
- trend metadata and history run count.
