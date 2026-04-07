# Phase 4 Batch 5 Incident Playbooks

Playbooks provide decision trees and standard operating procedures for repeated incident patterns.

## Playbook A: Bronze Freshness Degradation

### Trigger
- Incident type: FRESHNESS
- Layer: Bronze

### Workflow
1. Check source extraction job completion timestamp.
2. Validate Airbyte sync status and retries.
3. If sync failed: rerun ingestion window.
4. If sync succeeded but delay persists: investigate source API latency.
5. Add remediation note and update incident state.

### Exit Criteria
- Bronze freshness monitor returns healthy state for next run.

## Playbook B: Silver Volume Anomaly

### Trigger
- Incident type: VOLUME
- Layer: Silver

### Workflow
1. Compute Bronze-to-Silver pass-through ratio.
2. Compare ratio with 7-day baseline from anomaly learning output.
3. If ratio outside confidence band: inspect join and filters.
4. Rebuild impacted Silver models and rerun tests.

### Exit Criteria
- Row-count ratio returns to expected baseline band.

## Playbook C: Gold Schema Incident

### Trigger
- Incident type: SCHEMA
- Layer: Gold

### Workflow
1. Freeze downstream publication to BI consumers.
2. Diff schema from prior successful run.
3. Validate model contract changes with analytics owner.
4. Apply backward-compatible fix or controlled migration.
5. Resume publication and resolve incident.

### Exit Criteria
- Gold schema monitor healthy and downstream queries validated.

## Playbook D: Repeat Offender Monitor

### Trigger
- Same monitor produces incidents in at least 3 runs within 7 days.

### Workflow
1. Use anomaly learning artifact to inspect historical outliers.
2. Review adaptive threshold suggestion and confidence bounds.
3. Tune monitor threshold if justified by seasonal behavior.
4. Add a permanent issue for long-term upstream fix.

### Exit Criteria
- Monitor incident frequency drops below repeat threshold.

## Ownership Matrix
- Data Engineering: ingestion and transformation failures.
- Analytics Engineering: semantic and contract regressions.
- Platform Team: scheduling, infrastructure, and alerting pipeline issues.
