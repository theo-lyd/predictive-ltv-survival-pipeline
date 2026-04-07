# predictive-ltv-survival-pipeline
An end-to-end Analytics Engineering system built on Databricks and dbt. Features automated data synthesis, Survival Analysis (Kaplan-Meier) via dbt-Python, and rigorous observability using Monte Carlo and Great Expectations to track the lifecycle of B2B subscription cohorts. #dbt #databricks #pyspark #unit-economics #survival-analysis #ltv #airflow

## Documentation Index

### Strategic Documents (Phase 0 Planning)
1. [Project Brief](docs/01_project_brief.md) - Strategic thesis, objectives, scope, risks
2. [Phase-by-Phase Implementation Plan](docs/02_phase_by_phase_implementation_plan.md) - Detailed phase breakdown with acceptance criteria
3. [Requirement Specification Document](docs/03_requirement_specification_document.md) - Formal FR/NFR/BR/SR requirements
4. [Business Blueprint for Managers](docs/04_business_blueprint_for_managers.md) - Non-technical strategic decision framework

### Reference Documents
5. [Batch Documentation Report Template](docs/05_batch_documentation_report.md)
6. [Command Log Template](docs/06_command_log.md)
7. [Master Thesis Report Template](docs/07_master_thesis_report.md)
8. [Non-Technical Executive Report](docs/08_non_technical_executive_report.md)
9. [Beginner Walkthrough](docs/09_beginner_walkthrough.md)
10. [Seminar and Thesis Defense Brief](docs/10_seminar_and_thesis_defense_brief.md)
11. [Interview Questions and Answers](docs/11_interview_questions_and_answers.md)
12. [Implementation Scaffold Report](docs/12_implementation_scaffold_report.md)
13. [Implementation Command Log](docs/13_implementation_command_log.md)

### Governance & Security
- [Contributing Guide](CONTRIBUTING.md) - Contribution standards, validation requirements, and PR expectations
- [Security Policy](SECURITY.md) - Vulnerability reporting and response commitments
- [Branch Protection Required Checks](docs/BRANCH_PROTECTION_REQUIRED_CHECKS.md) - Required CI checks, review policy, and admin settings baseline

### Phase 0: Environment & Infrastructure Documentation
- [Environment Setup Guide](ENVIRONMENT_SETUP.md) - Step-by-step new contributor onboarding
- [System Architecture](ARCHITECTURE.md) - High-level design, Medallion layers, technology stack
- [Phase 0 Batch Completion Summary](docs/PHASE_0_BATCH_COMPLETION_SUMMARY.md) - Complete record of all 5 batches, issues resolved, validation results
- [Phase 0 Command Log](docs/PHASE_0_COMMAND_LOG.md) - Git, bash, pytest, dbt commands with examples
- [Phase 0 Acceptance Criteria](docs/PHASE_0_ACCEPTANCE_CRITERIA.md) - Go/no-go checklist for infrastructure completion

### Phase 1: Ingestion & Bronze Documentation
- [Phase 1 Implementation Report](docs/PHASE_1_IMPLEMENTATION_REPORT.md) - Batch-by-batch implementation with methodology and package rationale
- [Phase 1 Command Log](docs/PHASE_1_COMMAND_LOG.md) - End-to-end generation, ingestion, and validation commands

### Phase 2: Silver & Trusted Core Documentation
- [Phase 2 Implementation Report](docs/PHASE_2_IMPLEMENTATION_REPORT.md) - Silver transformation architecture, GE controls, and acceptance coverage
- [Phase 2 Command Log](docs/PHASE_2_COMMAND_LOG.md) - Reproducible Phase 2 build/validate command set
- [Phase 2 Silver Data Dictionary](docs/PHASE_2_SILVER_DATA_DICTIONARY.md) - Core Silver entities, grain, and field semantics
- [Phase 2 Contract Assumptions](docs/PHASE_2_CONTRACT_ASSUMPTIONS.md) - Null-handling strategy and deterministic business-key assumptions

### Phase 3: Gold Modeling & Thesis Engine Documentation
- [Phase 3 Implementation Report](docs/PHASE_3_IMPLEMENTATION_REPORT.md) - Gold metrics, predictive models, and acceptance mapping
- [Phase 3 Command Log](docs/PHASE_3_COMMAND_LOG.md) - Build, run, and validation command flow for advanced modeling
- [Phase 3 Technical Note](docs/PHASE_3_TECHNICAL_NOTE.md) - Statistical assumptions and interpretation guidance

### Phase 4: Orchestration & Observability Documentation (In Progress)
- [Phase 4 Implementation Plan](docs/PHASE_4_IMPLEMENTATION_PLAN.md) - Strategic plan with 5-batch breakdown, acceptance criteria, risk mitigation
- [Phase 4 Batch 1 Completion Report](docs/PHASE_4_BATCH_1_COMPLETION_REPORT.md) - Airflow setup, DAG skeleton, configuration, "why" decisions
- [Phase 4 Batch 1 Command Log](docs/PHASE_4_BATCH_1_COMMAND_LOG.md) - Reproducible commands for environment setup and validation
- [Phase 4 Batch 2 Completion Report](docs/PHASE_4_BATCH_2_COMPLETION_REPORT.md) - Core DAG implementation, custom operators, Airbyte integration, "why" decisions
- [Phase 4 Batch 2 Command Log](docs/PHASE_4_BATCH_2_COMMAND_LOG.md) - Reproducible commands for operators, sensors, and DAG validation
- [Phase 4 Batch 3 Completion Report](docs/PHASE_4_BATCH_3_COMPLETION_REPORT.md) - Resilience patterns, retry policies, Slack notifications, real operator integration
- [Phase 4 Batch 3 Command Log](docs/PHASE_4_BATCH_3_COMMAND_LOG.md) - Reproducible commands for error handling, pooling, and observability setup
- [Phase 4 Batch 4 Completion Report](docs/PHASE_4_BATCH_4_COMPLETION_REPORT.md) - Monte Carlo Data quality monitoring, health checks, incident routing, alert handlers
- [Phase 4 Batch 4 Command Log](docs/PHASE_4_BATCH_4_COMMAND_LOG.md) - Reproducible commands for Monte Carlo setup, configuration, and integration
- [Phase 4 Batch 5 Completion Report](PHASE_4_BATCH_5_COMPLETION_REPORT.md) - Dashboards, runbooks, automated remediation, and anomaly learning
- [Phase 4 Batch 5 Command Log](PHASE_4_BATCH_5_COMMAND_LOG.md) - Reproducible commands for validating Batch 5 observability tasks
- [Phase 4 Batch 5.1 Hardening Report](PHASE_4_BATCH_5_1_HARDENING_REPORT.md) - Failure policy decision, retries/timeouts, unit tests, compatibility fixes, and rationale
- [Phase 4 Batch 5.1 Command Log](PHASE_4_BATCH_5_1_COMMAND_LOG.md) - Commands used for variable setup, task-level validation, and warning-resolution checks

### Phase 5: BI & AI-Supported Storytelling Documentation
- [Phase 5 Implementation Plan](docs/PHASE_5_IMPLEMENTATION_PLAN.md) - Batch/chunk breakdown for complete executive dashboard delivery
- [Phase 5 Batch 1 Completion Report](docs/PHASE_5_BATCH_1_COMPLETION_REPORT.md) - Modular dashboard foundation and core visual components
- [Phase 5 Batch 1 Command Log](docs/PHASE_5_BATCH_1_COMMAND_LOG.md) - Commands for schema profiling and dashboard module setup
- [Phase 5 Batch 2 Completion Report](docs/PHASE_5_BATCH_2_COMPLETION_REPORT.md) - AI narrative workflow and Airflow integration
- [Phase 5 Batch 2 Command Log](docs/PHASE_5_BATCH_2_COMMAND_LOG.md) - Commands for DAG integration and task registration validation
- [Phase 5 Batch 3 Completion Report](docs/PHASE_5_BATCH_3_COMPLETION_REPORT.md) - Role views, glossary, latency validation, and QA completion
- [Phase 5 Batch 3 Command Log](docs/PHASE_5_BATCH_3_COMMAND_LOG.md) - Commands for tests, latency checks, and local app run
- [Phase 5 Batch Completion Summary](docs/PHASE_5_BATCH_COMPLETION_SUMMARY.md) - Consolidated acceptance mapping and strategic-question coverage
- [Phase 5 Audit Findings and Corrections (2026-04-07)](docs/PHASE_5_AUDIT_FINDINGS_AND_CORRECTIONS_2026_04_07.md) - Expert-level audit with implemented fixes and optimization backlog

### Audit & Corrections
- [Audit Findings and Corrections](docs/AUDIT_FINDINGS_AND_CORRECTIONS.md) - Phase 1-3 audit report, high/medium severity findings, and applied corrections
- [Phase 4 Audit Findings and Corrections (2026-04-07)](docs/PHASE_4_AUDIT_FINDINGS_AND_CORRECTIONS_2026_04_07.md) - Comprehensive Phase 4 production-readiness audit with implemented fixes and optimization notes

### Phase 7: Production Hardening & Enterprise Readiness
- [Phase 7 Implementation Plan](docs/PHASE_7_IMPLEMENTATION_PLAN.md) - Batch roadmap for access, observability, compliance, and hardening
- [Access Control Policy](docs/ACCESS_CONTROL_POLICY.md) - Role-to-capability mapping and enforcement model
- [Operations Status Guide](docs/OPERATIONS_STATUS_GUIDE.md) - Operational trend interpretation and escalation rules
- [Compliance Artifact Schema](docs/COMPLIANCE_ARTIFACT_SCHEMA.md) - Audit bundle JSON contract
- [Compliance Audit Process](docs/COMPLIANCE_AUDIT_PROCESS.md) - Daily/weekly/monthly compliance workflow
- [SLA Review Cadence](docs/SLA_REVIEW_CADENCE.md) - Expected review rhythm and ownership model
- [Recovery Playbooks](docs/RECOVERY_PLAYBOOKS.md) - Common failure recovery and cache refresh steps
- [Reprocessing Guide](docs/REPROCESSING_GUIDE.md) - Rebuild flow for SLA, snapshot, and audit artifacts

## GitHub Actions Polling (Token-Based)

Use authenticated polling in this container to avoid unauthenticated API rate limits.

1. Export a GitHub token with read access to repository actions:
	- `export GITHUB_TOKEN=...`
2. Poll the latest runs:
	- `python scripts/poll_workflow_runs.py --limit 10`
3. Poll runs for a specific commit SHA:
	- `python scripts/poll_workflow_runs.py --sha <sha-prefix> --limit 20`
4. Wait until filtered runs are complete (non-zero exit on timeout):
	- `python scripts/poll_workflow_runs.py --sha <sha-prefix> --wait --timeout-seconds 1200`

You can also use the Make target:
- `make actions-poll`

## Identity-Backed Access Model

Role access for Streamlit pages now derives from identity claim environment variables instead of an interactive role selector.

Required claim environment variable:
- `APP_USER_ROLE` with one of: `Executive`, `RevOps`, `Finance`, `Sales Leadership`

Optional identity metadata:
- `APP_USER_EMAIL`
- `APP_IDENTITY_SOURCE`

If `APP_USER_ROLE` is missing or invalid, the app defaults to least privilege (`Sales Leadership`).

## Dependency Lock Workflow

Pinned lock files:
- `requirements-lock.txt`
- `requirements-dev-lock.txt`

Commands:
1. Regenerate lock files:
	- `make lock-deps`
2. Validate lock files are current:
	- `make lock-check`

The canonical CI pipeline enforces lock drift checks through the `Dependency Lock Check` job.

## SLA Artifact Integrity Verification

The SLA monitor/export flow writes an integrity manifest with SHA-256 checksums. If `SLA_INTEGRITY_SIGNING_KEY` is set, the manifest is also HMAC-signed.

Verify integrity locally:
- `make verify-integrity`
- or `python scripts/verify_integrity_manifest.py --manifest <path>`
