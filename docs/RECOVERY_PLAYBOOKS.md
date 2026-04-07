# Recovery Playbooks

This guide covers common Phase 7 Batch 4 failures and the fastest safe recovery path.

## 1. Stale Dashboard or Ops Status View

Symptoms:
- Streamlit page shows older metrics than expected.
- Score or grade appears unchanged after a fresh pipeline run.

Recovery steps:
1. Rebuild the source artifacts:

```bash
make sla-monitor
make compliance-audit
```

2. Clear Streamlit cache if the UI still looks stale:

```bash
streamlit cache clear
```

3. Restart the Streamlit app.
4. Confirm the dashboard snapshot timestamp changed:
- `dashboard_snapshot_timestamp()`
- `narrative_snapshot_timestamp()`

Why this works:
- The Streamlit cache keys are derived from snapshot timestamps in the shared UI layer, so new source files invalidate cached data automatically.

## 2. Failed SLA Monitor Run

Symptoms:
- `make sla-monitor` returns non-zero.
- Alert payloads are emitted for breaches.
- History file is missing or empty.

Recovery steps:
1. Inspect the current report and history output.
2. Re-run the monitor with explicit output paths:

```bash
python scripts/monitor_sla_compliance.py \
  --output logs/sla_report.json \
  --history-file logs/sla_history.jsonl \
  --audit-output logs/compliance_audit.json
```

3. Verify the latest breach owners and actions in the output.
4. Re-run after fixing the upstream data issue.

## 3. Failed Compliance Export

Symptoms:
- `scripts/export_compliance_audit.py` fails.
- Missing history or report inputs.

Recovery steps:
1. Regenerate the source report with the monitor.
2. Re-export the audit bundle:

```bash
python scripts/export_compliance_audit.py \
  --output logs/compliance_audit.json \
  --report-file logs/sla_report.json \
  --history-file logs/sla_history.jsonl
```

3. If history is unavailable, let the exporter build from the current SLA report only.

## 4. Latency Regression

Symptoms:
- Dashboard or compliance validation is noticeably slower.
- `make phase7-latency` fails.

Recovery steps:
1. Check whether a large data artifact was added or regenerated.
2. Confirm the relevant snapshot timestamp changed and cache invalidation is working.
3. Re-run the latency validator after restart:

```bash
make phase7-latency
```

4. If latency still exceeds budget, inspect recent data growth and chart generation paths.

## 5. GitHub Actions Failure After Batch 4

Symptoms:
- CI or Enhanced CI/CD fails after a recovery change.

Recovery steps:
1. Poll the run with the authenticated helper:

```bash
python scripts/poll_workflow_runs.py --sha <commit-sha> --wait --timeout-seconds 1200
```

2. Fix the failing step locally.
3. Re-run `make test` and the relevant `make phase7-*` target.
4. Push a fix-forward commit on `master`.
