# SLA Review Cadence

This document defines review frequency, ownership, and expected outputs for SLA compliance operations.

## Cadence Overview

1. Daily
- Owner: On-call Analytics Engineer
- Inputs: SLA dashboard, operations status page, compliance artifact
- Output: Daily check confirmation and incident escalation if required

2. Weekly
- Owner: Analytics Engineering Lead + Data Quality Lead
- Inputs: Weekly compliance artifact and SLA trend sections
- Output: Governance review note with remediation priorities

3. Monthly
- Owner: Data Governance Council
- Inputs: Monthly artifact roll-up and incident summaries
- Output: Sign-off record and policy adjustments

## Daily Checklist

1. Verify latest grade and overall score.
2. Check breach and warning movement from previous run.
3. Confirm contract validity status.
4. Escalate immediately on new P1 breach.
5. Archive or reference the day artifact path in operations notes.

## Weekly Checklist

1. Run compliance export from current report and history.
2. Compare trend deltas across recent runs.
3. Review unresolved breaches and aging warnings.
4. Verify owners and channels remain correct in evidence records.
5. Publish short governance summary with explicit actions.

## Monthly Checklist

1. Consolidate weekly outputs and incident outcomes.
2. Review recurring root causes and control effectiveness.
3. Confirm retention policy is being followed.
4. Document approved policy or threshold changes.
5. Store signed monthly compliance package in audit archive.

## Escalation Triggers

Escalate when any condition is true:
- grade decreases by one or more bands between consecutive runs,
- breach count increases over prior run,
- contract validity changes from true to false,
- repeated breach persists across three or more runs.

## Expected Artifact Paths

Suggested default paths:
- `logs/sla_report.json`
- `logs/sla_history.jsonl`
- `logs/compliance_audit.json`

Optional review outputs:
- `logs/compliance_audit_weekly.json`
- `logs/compliance_audit_monthly.json`
