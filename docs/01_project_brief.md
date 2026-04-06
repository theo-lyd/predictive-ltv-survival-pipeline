# Project Brief

## Project Title
LTV and Unit Economics Analytics for Subscription Growth

## Thesis Statement
Evaluating the correlation between early-stage discount usage and long-term Customer Lifetime Value (LTV) in B2B SaaS using a survival analysis approach.

## Executive Context
B2B SaaS teams often optimize for top-line growth and volume, but aggressive discounting can create low-quality cohorts that churn quickly after promotional periods. This capstone builds a production-grade analytics engine to quantify whether early discount strategy drives sustainable value or toxic growth.

The project combines cloud-native data engineering, analytics engineering, advanced modeling, and executive BI to answer a core strategic question:

Does high signup discounting (for example, 40-50%) correlate with short customer tenure and lower long-term LTV?

## Strategic Objectives
1. Build an end-to-end Medallion data platform (Bronze, Silver, Gold) on Databricks and Delta Lake.
2. Engineer a controlled research environment by augmenting Telecom Churn data with synthetic promotion metadata.
3. Validate data quality and business rules using Great Expectations and dbt tests.
4. Model discount impact on tenure and churn using Kaplan-Meier survival analysis and churn prediction.
5. Deliver an executive decision cockpit with cohort, survival, LTV/CAC, and what-if simulation views.
6. Operationalize the pipeline with orchestration, observability, CI/CD, SLAs, and governance.

## Scope
### In Scope
- Containerized development setup via GitHub Codespaces and devcontainer.
- Ingestion of hybrid sources: Kaggle churn dataset, synthetic XML/Parquet promotion data, and optional billing tables synced via Airbyte.
- Bronze append-only historical storage in Delta.
- Silver data cleaning, harmonization, deduplication, and identity resolution.
- Gold modeling for tenure, contribution margin, LTV, survival curves, and churn probability.
- Airflow orchestration with ingestion and transformation dependencies.
- Observability for freshness, volume anomalies, schema drift, and pipeline reliability.
- Executive dashboard and AI-assisted narrative layer.

### Out of Scope
- Full enterprise CRM migration.
- Production legal/privacy implementation across all geographies.
- Real-time streaming architecture beyond planned batch/near-real-time ingestion.

## Data and Research Design
### Primary Data Sources
- Telecom Customer Churn dataset (base behavioral substrate).
- Synthetic Promotion Dimension generated in-code (discount type, percent, start/end dates, channel tags).
- Optional Airbyte-fed billing data from Postgres/MySQL.

### Hybrid Augmentation Rationale
The hybrid approach is intentionally selected to ensure analytical signal quality while preserving realistic pipeline complexity. Synthetic generation enables controlled correlation structures (for example, deeper discounts linked to short-tenure cohorts) and introduces intentional data quality defects to test transformation rigor.

### Intentional Data Friction
Generated promotion data includes:
- Null discount values.
- Inconsistent date formats.
- Duplicate promotion IDs.
- Mixed encoding edge cases.

This creates a defensible demonstration of real-world analytics engineering under non-ideal conditions.

## Platform and Technology Stack
- Compute and storage: Databricks + Delta Lake.
- Transformation: dbt-databricks, dbt SQL models, dbt Python models.
- Processing: PySpark and Databricks notebooks.
- Orchestration: Apache Airflow.
- Ingestion: Spark Autoloader + Airbyte.
- Data quality: Great Expectations + dbt tests.
- Observability: Monte Carlo.
- Governance and lineage: Unity Catalog.
- BI and AI: Streamlit/Metabase + LLM-assisted narrative summaries.
- CI/CD: GitHub Actions with slim CI (`state:modified`).

## Medallion Architecture Summary
- Bronze: Immutable append-only raw ingestion preserving full historical audit trails.
- Silver: Standardization and trust layer for casting, deduplication, quality checks, and identity stitching.
- Gold: Business-ready semantic and predictive layer including LTV, survival outputs, and decision KPIs.

## Business Rules to Encode
- Churn rule: Customer considered hard-churned if inactive for more than 30 days.
- LTV window cap: 36-month rolling horizon.
- Net revenue logic: LTV net of discounts, acquisition, and service costs.
- Heavy promotion flag: Discounts greater than 15%.
- CAC payback definition: Profitable only once cumulative contribution margin exceeds CAC.
- Financial consistency rule: Final invoice price must equal original price minus discount amount.

## Key Analytical Questions
1. Does a 50% signup discount correlate with tenure under 6 months?
2. Which channels produce the highest LTV/CAC ratio?
3. Which behavioral and promotional features most strongly predict churn in the next 60 days?
4. What is the expected NRR impact if average discounts are reduced by 5%?

## Success Metrics
- 10% reduction in acquisition of high-discount/high-churn cohorts.
- 15% improvement in LTV/CAC via budget reallocation to high-tenure channels.
- 100% elimination of cross-functional metric drift for core KPIs.
- Gold layer freshness SLA adherence: data updated within 6 hours of business day start.

## Deliverables
1. Reproducible cloud-native development environment.
2. Production-style Medallion pipeline and tested transformations.
3. Gold data products including `fct_customer_ltv` and survival cohort outputs.
4. Churn propensity model and discount sensitivity outputs.
5. Executive Flight Deck dashboard with what-if simulator and AI narrative.
6. CI/CD, observability alerts, and governance lineage evidence.

## Risks and Mitigations
- Risk: Synthetic bias overstates real-world effect sizes.
Mitigation: Clearly separate synthetic assumptions, run sensitivity analyses, and report confidence bounds.

- Risk: Schema evolution breaks downstream transformations.
Mitigation: Autoloader schema handling, versioned models, and observability alerts.

- Risk: Data trust erosion from inconsistent metric logic.
Mitigation: Centralized business rules in dbt and automated GE/dbt validation gates.

## Intended Audience
- Data Engineering and Analytics Engineering teams.
- RevOps, Finance, Sales leadership.
- Executive stakeholders requiring pricing and growth strategy visibility.

## Brief Outcome Statement
This project delivers an economic decision engine that converts fragmented, noisy subscription data into a governed and predictive intelligence system. It enables leadership to balance growth velocity with durable unit economics by quantifying the long-term consequences of discount policy.