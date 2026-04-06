# Master Thesis Report

## Title
LTV and Unit Economics Analytics for Subscription Growth

## Abstract
This thesis proposes and documents a cloud-native analytics engineering system that evaluates whether early-stage discounting correlates with long-term customer value in B2B SaaS. The solution combines a Medallion architecture on Databricks, dbt-based transformation and testing, synthetic promotion generation for controlled signal design, survival analysis for cohort behavior, and an executive dashboard for decision support. The expected contribution is a reproducible framework for quantifying how discount policy affects retention, LTV, and profitability.

## Research Problem
Many SaaS teams grow revenue by increasing discount intensity, yet these customers may churn quickly and generate poor unit economics. The thesis investigates whether discounting at signup is associated with shorter tenure and lower LTV, and whether those effects are visible through survival analysis and cohort-level reporting.

## Thesis Statement
Evaluating the correlation between early-stage discount usage and long-term Customer Lifetime Value in B2B SaaS using a survival analysis approach.

## Research Objectives
1. Build a governed data pipeline from raw sources to decision-ready metrics.
2. Synthesize a promotion dimension that creates a measurable discount signal.
3. Clean and harmonize subscription, billing, and promotion data.
4. Estimate survival curves for discounted and non-discounted cohorts.
5. Compute LTV, CAC, NRR, and discount efficiency metrics.
6. Deliver executive-level interpretations and what-if analysis.

## Methodology
The methodology is structured in six stages:
- Environment and infrastructure setup.
- Bronze ingestion with immutable append-only history.
- Silver standardization and quality validation.
- Gold feature engineering and modeling.
- Orchestration and observability.
- BI and governance for stakeholder consumption.

The analytical backbone is a hybrid dataset design. A base churn dataset is augmented with synthetic promotion metadata to create controlled exposure to different discount regimes. This approach allows the thesis to test whether promotional intensity is associated with churn behavior while still demonstrating production-grade engineering patterns.

## Data Design
Primary inputs include customer churn records, optional billing data, and synthetic promotion data. Promotion records encode discount type, percent, dates, and channel context. The data intentionally includes imperfect records so that transformation logic, quality checks, and auditability can be demonstrated.

## Architecture Summary
- Bronze: raw, immutable, append-only storage.
- Silver: trusted, cleaned, and conformed source of truth.
- Gold: analytical and predictive metrics including LTV and survival curves.
- Governance: Unity Catalog lineage and controlled access.
- Orchestration: Airflow and alerting/observability.

## Modeling Approach
The thesis uses Kaplan-Meier survival analysis to compare discounted and non-discounted cohorts. It also defines a discount intensity index and can extend to churn classification using SparkML or scikit-learn. The focus is on interpreting differences in retention patterns rather than claiming causal proof.

## Evaluation Criteria
- Data quality checks pass consistently.
- Survival curves produce interpretable cohort separation.
- LTV calculations respect business rules and cost logic.
- Dashboard outputs answer the board-level questions.

## Key Contributions
1. A reproducible end-to-end analytics engineering blueprint.
2. A controlled promotional data generation strategy for thesis signal design.
3. A formalized business-rule layer for LTV and churn definitions.
4. An executive interface for pricing and retention decisions.

## Limitations
- Synthetic augmentation can overstate effect sizes if not clearly disclosed.
- The system is designed to establish correlation and operational insight, not causal proof.
- Final results depend on the quality and completeness of the original source data.

## Conclusion
This thesis demonstrates how analytics engineering, survival analysis, and governed BI can be combined to turn raw subscription data into a strategic unit economics engine for management decision-making.
