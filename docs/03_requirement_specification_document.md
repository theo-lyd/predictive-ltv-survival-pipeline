# Requirement Specification Document (RSD)

## Document Control
- Project: LTV and Unit Economics Analytics for Subscription Growth
- Version: 1.0
- Status: Baseline Draft
- Primary Owner: Analytics Engineering
- Stakeholders: RevOps, Finance, Sales Ops, Data Platform, Executive Sponsors

## 1. Purpose
This document defines the formal requirements for designing, building, validating, and operating a cloud-native analytics system that evaluates how early-stage discounts influence long-term tenure, churn, and LTV in a B2B SaaS setting.

## 2. Scope
### 2.1 In Scope
- End-to-end Medallion data pipeline (Bronze, Silver, Gold).
- Hybrid dataset strategy (baseline churn + synthetic promotions).
- Survival analysis and churn prediction in Databricks/dbt Python models.
- Executive-facing BI outputs and AI-generated narrative summaries.
- Operational controls (orchestration, observability, CI/CD, SLAs, governance).

### 2.2 Out of Scope
- Global legal compliance implementation across all jurisdictions.
- Real-time event streaming architecture beyond planned ingestion intervals.
- Enterprise-wide CRM replacement.

## 3. Business Objectives and Success Criteria
1. Quantify correlation between discount intensity and churn/tenure outcomes.
2. Improve unit economics decision quality (LTV/CAC and NRR sensitivity).
3. Standardize KPI logic across Finance, Sales, and RevOps.
4. Deliver actionable decision tools to management.

Target business outcomes:
- 10% reduction in high-discount/high-churn acquisition.
- 15% improvement in LTV/CAC via channel reallocation.
- 100% elimination of KPI metric drift across teams.

## 4. Stakeholders and User Personas
- Executive Sponsor: needs strategic KPI and risk signal clarity.
- RevOps Manager: needs discount policy optimization guidance.
- Finance Manager: needs trusted LTV/CAC and margin accounting.
- Sales Leadership: needs pricing elasticity and what-if impact visibility.
- Data Engineering: needs stable ingestion and lineage.
- Analytics Engineering: needs tested semantic and modeling layers.

## 5. Assumptions and Constraints
### Assumptions
- Databricks workspace and compute access are available.
- GitHub Actions and secrets are configured.
- Source datasets are legally and operationally usable.

### Constraints
- Primary development in GitHub Codespaces.
- Core implementation stack: Databricks, dbt, PySpark, Airflow.
- Gold layer freshness SLA: within 6 hours of business day start.

## 6. Functional Requirements

## 6.1 Environment and Platform
- FR-001: The system shall provide a reproducible development environment via `.devcontainer`.
- FR-002: The environment shall include Python 3.10, Java runtime, Databricks CLI, and `dbt-databricks`.
- FR-003: The system shall support secure Databricks connectivity through secret-backed credentials.

## 6.2 Data Ingestion (Bronze)
- FR-010: The system shall ingest base churn data into Bronze Delta tables.
- FR-011: The system shall ingest synthetic promotion metadata in XML and/or Parquet.
- FR-012: The system shall support append-only historical persistence for Bronze tables.
- FR-013: The ingestion flow shall process files with variable metadata headers using skip logic.
- FR-014: The ingestion flow shall support UTF-8 and Latin-1 decoding fallback.
- FR-015: The ingestion flow shall normalize shorthand numeric forms (for example, K, Mio) to numeric values.
- FR-016: The ingestion layer shall support incremental ingestion using Spark Autoloader.
- FR-017: The ingestion layer shall support optional Airbyte sync for Postgres/MySQL billing sources.

## 6.3 Synthetic Data Augmentation
- FR-020: The system shall generate a promotion dimension mapped by customer ID.
- FR-021: The generator shall assign discount types (`Early Bird`, `Seasonal`, `None`).
- FR-022: The generator shall assign discount percentages in a controlled range (0-50%).
- FR-023: The generator shall inject tenure-correlated discount intensity to create analytical signal.
- FR-024: The generator shall intentionally include dirty data patterns (null discounts, duplicate IDs, inconsistent date formats).
- FR-025: The generator shall support deterministic runs via configurable random seed.

## 6.4 Data Transformation (Silver)
- FR-030: The system shall cast and standardize currencies and timestamps to canonical types.
- FR-031: The system shall deduplicate records by defined business keys and recency logic.
- FR-032: The system shall resolve customer identity across billing and promotion datasets.
- FR-033: The system shall classify discounts into cohorts (for example, heavy promotion >15%).
- FR-034: The system shall persist curated Silver entities as trusted source-of-truth tables.

## 6.5 Data Quality and Validation
- FR-040: The system shall execute dbt tests on key model constraints.
- FR-041: The system shall execute Great Expectations checkpoints for financial and temporal logic.
- FR-042: The system shall validate that MRR values are never negative.
- FR-043: The system shall validate that discount start dates occur before churn dates.
- FR-044: The system shall validate invoice arithmetic consistency (`final_invoice_price = original_price - discount_amount`).
- FR-045: The system shall fail pipeline quality gates when critical validations fail.

## 6.6 Gold Modeling and Analytics
- FR-050: The system shall compute customer tenure and contribution margin features.
- FR-051: The system shall compute a discount intensity index.
- FR-052: The system shall implement Kaplan-Meier survival curves for discount-based cohorts.
- FR-053: The system shall train or score a churn prediction model for active customers.
- FR-054: The system shall publish a `fct_customer_ltv` fact table net of discount and cost components.
- FR-055: The system shall cap LTV projection to a 36-month rolling window.

## 6.7 Orchestration and Scheduling
- FR-060: The platform shall orchestrate end-to-end runs via Airflow DAGs.
- FR-061: Airflow shall include file-arrival sensors for new ingestion triggers.
- FR-062: DAG sequence shall execute ingestion, Bronze processing, and dbt transformations in dependency order.
- FR-063: Orchestration shall include retries, timeout policies, and failure notifications.

## 6.8 Observability and SLA
- FR-070: The platform shall monitor data freshness, volume anomalies, and schema evolution.
- FR-071: The platform shall alert when discount usage drops unexpectedly to 0% (potential ingestion fault).
- FR-072: The platform shall alert on Gold freshness SLA breach beyond 6 hours.
- FR-073: The platform shall provide run-level diagnostics and incident traceability.

## 6.9 BI and AI Interface
- FR-080: The system shall provide an executive dashboard with global filters and KPI ribbon.
- FR-081: The dashboard shall include a cohort heatmap by entry period and discount tier.
- FR-082: The dashboard shall include survival curve comparisons across discount cohorts.
- FR-083: The dashboard shall include what-if simulation for discount-rate impact on NRR.
- FR-084: The dashboard shall include LTV/CAC and discount efficiency KPIs.
- FR-085: The platform shall provide an AI narrative summary grounded in current Gold-layer data.

## 6.10 CI/CD and Governance
- FR-090: Every pull request shall trigger automated dbt and data quality tests.
- FR-091: CI pipeline shall support slim execution based on modified dbt state.
- FR-092: The system shall record lineage from raw discount data to final LTV metrics via Unity Catalog.
- FR-093: Governance artifacts shall include data dictionary, metric definitions, and ownership mapping.

## 7. Non-Functional Requirements

## 7.1 Performance
- NFR-001: Daily end-to-end pipeline shall complete within agreed processing window.
- NFR-002: Dashboard primary views shall render within acceptable interactive latency under expected load.

## 7.2 Reliability and Availability
- NFR-010: Pipeline shall support automated retry and idempotent re-runs where applicable.
- NFR-011: Critical failures shall emit alerts with actionable context.

## 7.3 Security
- NFR-020: Secrets shall not be hard-coded in repository files.
- NFR-021: Access to production schemas shall be role-based and least-privilege.

## 7.4 Data Integrity
- NFR-030: Bronze data shall remain immutable append-only.
- NFR-031: Metric definitions shall be centralized and version controlled.

## 7.5 Maintainability
- NFR-040: Models, jobs, and checks shall be documented with ownership.
- NFR-041: CI/CD shall provide fast feedback to maintain developer productivity.

## 8. Data Requirements

## 8.1 Core Entities
- Customer
- Subscription
- Billing Transaction
- Promotion
- Channel Attribution
- Cohort
- Churn Event

## 8.2 Required Fields (Minimum)
- Customer key, subscription key, event timestamps, currency amounts, discount amount/percent/type, channel, churn indicator/date, acquisition cost components.

## 8.3 Data Quality Thresholds
- Null tolerance for critical keys: 0%.
- Duplicate tolerance for primary business keys in Silver/Gold: 0%.
- Freshness tolerance for Gold tables: less than or equal to 6 hours from business day start.

## 9. Business Rules (Formalized)
- BR-001: Hard churn is defined as no active subscription for more than 30 days.
- BR-002: Soft churn (downgrade/contraction) is tracked separately from hard churn.
- BR-003: Discounts greater than 15% are classified as heavy promotions.
- BR-004: LTV is net of discounts, acquisition costs, and service costs.
- BR-005: Profitability is reached when cumulative contribution margin exceeds CAC.
- BR-006: LTV estimation is capped to a 36-month rolling horizon.

## 10. Reporting and Decision Support Requirements
- RR-001: System shall answer whether deep signup discounts correlate with under-6-month tenure.
- RR-002: System shall rank channels by LTV/CAC ratio.
- RR-003: System shall identify highest-signal leading indicators for near-term churn risk.
- RR-004: System shall estimate NRR impact of discount policy adjustments.

## 11. Test and Acceptance Requirements

## 11.1 Functional Acceptance
- FAR-001: All FR requirements mapped to implemented components and validated tests.
- FAR-002: End-to-end DAG run completes successfully in target environment.

## 11.2 Data Acceptance
- DAR-001: Silver/Gold row-level reconciliation and aggregate checks pass.
- DAR-002: All critical GE/dbt checks pass with no unresolved blockers.

## 11.3 Business Acceptance
- BAR-001: Stakeholders can answer four strategic questions directly from dashboard outputs.
- BAR-002: KPI values align with approved metric definitions and finance sign-off.

## 12. Traceability Matrix (Condensed)
- Thesis Question 1 -> FR-052, FR-054, RR-001, BR-001, BR-004.
- Thesis Question 2 -> FR-054, FR-084, RR-002, BR-005.
- Operational reliability -> FR-060 to FR-073, NFR-010, NFR-011.
- Governance trust -> FR-090 to FR-093, NFR-030, NFR-031.

## 13. Risks and Compliance Notes
- Synthetic signal risk: disclose assumptions and run sensitivity tests.
- Schema drift risk: enforce observability and schema contracts.
- Interpretation risk: annotate limitations for causality claims versus correlation.

## 14. Sign-Off Criteria
This RSD is considered approved when:
1. Data Engineering, Analytics Engineering, and Finance confirm requirement completeness.
2. RevOps and Sales Ops confirm business question coverage.
3. Executive sponsor approves success metrics and SLA thresholds.

## 15. Appendix: Suggested Requirement IDs by Layer
- ENV: FR-001 to FR-003
- BRONZE: FR-010 to FR-017
- SYNTH: FR-020 to FR-025
- SILVER: FR-030 to FR-034
- QUALITY: FR-040 to FR-045
- GOLD: FR-050 to FR-055
- ORCH: FR-060 to FR-063
- OBS: FR-070 to FR-073
- BI: FR-080 to FR-085
- CICD/GOV: FR-090 to FR-093