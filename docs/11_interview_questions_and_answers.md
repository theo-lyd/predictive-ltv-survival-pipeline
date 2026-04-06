# Interview Questions and Answers

## Technical Questions

### 1. Why did you use a Medallion architecture?
It gives a clean separation between raw ingestion, trusted transformation, and business-ready outputs. That makes the pipeline easier to validate, govern, and explain.

### 2. Why use synthetic promotion data?
The base dataset does not naturally contain the discount structure needed to test the thesis. Synthetic promotion data creates a controlled signal while still demonstrating realistic engineering complexity.

### 3. Why use survival analysis?
Survival analysis is a strong fit for time-to-churn problems because it models retention over time and compares cohort behavior directly.

### 4. Why combine dbt and Spark?
dbt is excellent for managed transformation logic and testing, while Spark handles heavier parsing, distributed processing, and complex ingestion tasks.

### 5. Why use Great Expectations and dbt tests together?
They cover complementary layers: dbt for model-level logic and GE for deeper validation of business and data quality rules.

### 6. What does append-only Bronze storage achieve?
It preserves a complete audit trail and makes it possible to trace issues back to raw source states.

### 7. How do you handle schema drift?
Use Autoloader-style incremental ingestion, schema monitoring, and observability alerts so changes are detected before they break downstream models.

### 8. How is LTV calculated?
LTV is computed net of discounts, acquisition costs, and service costs, with a 36-month rolling cap.

### 9. What is discount intensity index?
It is a derived feature that summarizes the magnitude and potential business impact of promotional treatment.

### 10. How do you avoid claiming causality?
The thesis is framed as correlation and cohort behavior analysis, not causal proof. That distinction is explicitly documented.

## Business Questions

### 11. Why does this matter to leadership?
It helps leadership stop unprofitable growth patterns and allocate budget toward customers and channels that produce durable value.

### 12. What business decisions does it support?
Discount guardrails, channel investment, retention targeting, and pricing policy review.

### 13. What is the main executive KPI?
LTV/CAC is the core board-level unit economics metric, supported by churn, NRR, and discount efficiency.

### 14. What makes the dashboard useful for managers?
It is built around decisions, not just charts: cohort views, survival comparison, what-if simulation, and AI narrative summaries.

### 15. How does this reduce metric drift?
The business rules are centralized in the transformation layer and enforced with automated tests and lineage.

## Project and Delivery Questions

### 16. How would you implement this in a team?
Start with environment setup, then Bronze ingestion, then Silver validation, then Gold modeling, then orchestration, dashboarding, and CI/CD.

### 17. What would you do first in a real deployment?
Lock down the business definitions and the data contracts before expanding the modeling layer.

### 18. How do you keep the project reproducible?
Use containerized development, version-controlled transformations, deterministic synthetic generation, and documented run order.

### 19. What are the biggest risks?
Synthetic bias, schema drift, metric inconsistency, and stakeholder misalignment.

### 20. What is the simplest summary of the project?
It is a governed analytics engine that shows whether discounting customers early helps or hurts long-term SaaS value.

### 21. How did you handle a Codespaces container recovery-mode failure?
I analyzed the creation log, identified an unsigned third-party Yarn apt source as the root cause, removed that source in the Docker build step, and added a validated post-create setup script to restore deterministic environment provisioning.
