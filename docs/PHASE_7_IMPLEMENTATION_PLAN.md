# Phase 7: Production Hardening and Enterprise Readiness Implementation Plan

## Objective
Turn the now-complete CI/CD, governance, lineage, and SLA foundation into a more operational platform by tightening access control, strengthening observability, automating compliance workflows, and improving performance and recovery paths.

---

## Phase 7 Strategy

Phase 7 should focus on the parts of the platform that matter once the governance layer exists:
- make access controls enforceable instead of informational,
- make SLA history actionable instead of just visible,
- make lineage and compliance easier to audit in practice,
- make failure recovery deterministic and documented,
- reduce operational friction for the people maintaining the pipeline.

This phase should be delivered in batches so each batch is testable and mergeable on its own.

---

## Batch Breakdown

### Batch 1: Identity, Access, and Role Enforcement
**Goals:**
- Move from documented RBAC to enforceable UI and workflow behavior
- Gate sensitive views and maintenance actions by role
- Add a clear policy surface for environment-level access assumptions

**Deliverables:**
- Role-aware Streamlit navigation and page access rules
- Centralized authorization helper functions
- Access-denied state handling and operator guidance
- Documentation for role-to-capability mapping

**Implementation Files:**
- `streamlit_app/core/auth.py` (new)
- `streamlit_app/core/ui.py` (extend role handling and gating helpers)
- `streamlit_app/app.py` (enforce page exposure rules at startup)
- `streamlit_app/pages/1_Executive_Flight_Deck.py` (gate executive-only views)
- `streamlit_app/pages/5_AI_Daily_Narrative.py` (gate narrative review surface)
- `streamlit_app/pages/7_SLA_Compliance.py` (gate SLA operations surface)
- `docs/ACCESS_CONTROL_POLICY.md` (new)
- `tests/test_phase7_access_control.py` (new)

**Implementation Steps:**
1. Add a single authorization helper that maps roles to allowed capabilities.
2. Update the app entrypoint to select available pages based on the current role.
3. Add an access-denied view that explains why a page is unavailable and who to contact.
4. Gate privileged actions such as SLA monitor reruns, alert dispatch, and operational exports.
5. Document the role-to-capability matrix and the fallback behavior for unauthenticated sessions.

**Acceptance Criteria:**
- A user with a restricted role cannot open pages or actions outside their allowed set.
- An unauthorized view renders a clear denial message instead of a stack trace or empty page.
- The authorization mapping is defined in one place and reused across pages.
- Tests cover at least one allowed path and one denied path for each protected surface.
- The documentation file lists every role and the capabilities it can access.

**Success Signal:**
- Restricted pages and actions are visibly gated by role
- Role-based behavior is testable without external auth infrastructure

---

### Batch 2: Operational Observability
**Goals:**
- Add live operational status views for pipeline health
- Surface SLA history, alert volume, and recent runs in one place
- Make warning and breach trends visible without opening logs

**Deliverables:**
- Enhanced SLA dashboard with trend summaries and breach history
- Operational status page for recent jobs and latest artifacts
- Reusable chart helpers for history and anomaly detection
- Lightweight local report export path for debugging

**Implementation Files:**
- `streamlit_app/pages/7_SLA_Compliance.py` (extend historical trend and alert sections)
- `streamlit_app/pages/8_Operations_Status.py` (new)
- `streamlit_app/core/charts.py` (extend with operational trend helpers)
- `streamlit_app/core/sla.py` (extend history shaping if needed)
- `scripts/export_operational_snapshot.py` (new)
- `tests/test_phase7_operational_observability.py` (new)
- `docs/OPERATIONS_STATUS_GUIDE.md` (new)

**Implementation Steps:**
1. Add a dedicated operations page that summarizes the latest SLA run, alert count, and history freshness.
2. Extend the SLA page with trend charts for score, grade, and breach counts over time.
3. Add export helpers that serialize the current operational snapshot for local debugging and incident review.
4. Reuse the existing JSONL history file so the dashboard and the export script read the same source of truth.
5. Document how operators should interpret PASS/WARN/FAIL history and when to escalate.

**Acceptance Criteria:**
- The SLA page shows both the current report and at least two historical trend visualizations.
- The operations page renders the latest run timestamp, score, grade, and breach count without requiring log access.
- The export script writes a structured snapshot artifact that can be used in incident notes.
- Tests cover chart generation, snapshot export, and missing-history fallback behavior.
- Documentation explains which page to use for quick status versus deeper operational review.

**Success Signal:**
- Operators can see what changed, when it changed, and whether it is getting better or worse

---

### Batch 3: Compliance Automation and Auditability
**Goals:**
- Turn SLA and governance rules into repeatable checks with artifacts
- Add auditable outputs for compliance reviews and incident postmortems
- Make the monitoring loop produce persistent evidence

**Deliverables:**
- Structured compliance artifact export
- Historical SLA and governance snapshot retention policy
- Audit-ready summaries for breaches, warnings, and remediations
- Documentation for review cadence and sign-off expectations

**Implementation Files:**
- `scripts/monitor_sla_compliance.py` (extend with audit export hooks)
- `scripts/export_compliance_audit.py` (new)
- `scripts/export_operational_snapshot.py` (new, shared snapshot shape)
- `streamlit_app/core/sla.py` (extend audit record generation if needed)
- `docs/COMPLIANCE_AUDIT_PROCESS.md` (new)
- `docs/SLA_REVIEW_CADENCE.md` (new)
- `docs/COMPLIANCE_ARTIFACT_SCHEMA.md` (new)
- `tests/test_phase7_compliance_audit.py` (new)

**Implementation Steps:**
1. Define a stable compliance artifact schema that captures run time, report grade, alert counts, and evidence references.
2. Extend the SLA monitor so each run can emit a machine-readable audit bundle alongside the report JSON.
3. Add an export script that aggregates SLA history into review-ready summaries for incidents and monthly governance reviews.
4. Make the export path reuse the same history source used by the dashboard so audit and UI views stay consistent.
5. Write the review cadence guide so operators know when daily, weekly, and monthly artifacts are expected.

**Acceptance Criteria:**
- The monitor can emit a compliance audit artifact without manual file edits.
- The export script produces a structured bundle that includes at least one current report and historical trend summary.
- The audit bundle references the same evidence fields shown in the SLA dashboard.
- Tests validate schema shape, export output, and missing-history fallback behavior.
- Documentation describes the cadence for daily checks, weekly review, and monthly sign-off.

**Success Signal:**
- Compliance evidence can be generated from the platform itself without manual reconstruction

---

### Batch 4: Performance, Recovery, and Release Hardening
**Goals:**
- Reduce operational drift in the dashboard and monitor paths
- Add recovery guidance for common failures
- Improve local and CI performance for the heaviest checks

**Deliverables:**
- Cache and snapshot invalidation review for Streamlit pages
- Recovery playbooks for failed scheduled runs and alert delivery
- Performance validation script for dashboard and monitor latency
- Documentation for rerun, rollback, and reprocess workflows

**Likely Files:**
- `scripts/validate_phase7_monitoring_latency.py` (new)
- `docs/RECOVERY_PLAYBOOKS.md` (new)
- `docs/REPROCESSING_GUIDE.md` (new)
- `Makefile` (new `phase7-*` or validation targets)

**Success Signal:**
- Common operational failures have a documented and tested recovery path

---

## Standards & Best Practices

### Access Control
- Enforce least privilege in the UI before external SSO is added
- Keep role behavior centralized so it can be tested in one place
- Prefer denial by default for sensitive workflows

### Observability
- Use historical trends instead of single-point status for operational decisions
- Keep warning thresholds conservative enough to avoid alert fatigue
- Store lightweight local artifacts for reproducibility

### Compliance
- Prefer machine-readable summaries for audits
- Keep human-facing explanations adjacent to the checks that generate them
- Ensure every alert can be tied to a specific evidence record

### Testing
- Add tests for both healthy and degraded states
- Validate history persistence and report shape, not just page rendering
- Keep performance validation separate from correctness tests

---

## Proposed Timeline
- Batch 1: 45-60 min
- Batch 2: 45-60 min
- Batch 3: 45-60 min
- Batch 4: 45-60 min

**Total:** ~3-4 hours

---

## Success Criteria
- Role enforcement is real, not just documented
- SLA history is visible and actionable in the UI
- Compliance checks produce durable audit artifacts
- Recovery paths for scheduled jobs and alerts are documented
- Monitoring and dashboard changes remain fast enough for day-to-day use

---

## Recommended Entry Point
Start with Batch 1 and Batch 2 in sequence only if access control needs to be operationalized immediately. Otherwise, Batch 2 can run first to stabilize observability while the auth surface is designed.
