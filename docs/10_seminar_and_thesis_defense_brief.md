# Seminar and Thesis Defense Brief

## Presentation Goal
Explain the research problem, the technical solution, the business value, and the evidence in a way that is clear to both technical and non-technical reviewers.

## Suggested Talk Track
1. Problem: discount-led growth can hide poor unit economics.
2. Research question: does early discounting correlate with lower LTV and shorter tenure?
3. Method: Medallion architecture, synthetic promotion design, survival analysis, and LTV modeling.
4. Results: compare cohort survival, churn risk, and discount efficiency.
5. Business impact: better pricing policy, better budget allocation, better retention.

## Recommended Slide Outline
1. Title and thesis statement.
2. Business problem and motivation.
3. Data sources and hybrid augmentation approach.
4. Architecture overview.
5. Bronze, Silver, and Gold implementation.
6. Survival analysis and LTV methodology.
7. Dashboard and decision layer.
8. Governance, testing, and observability.
9. Results and managerial interpretation.
10. Limitations and future work.

## Key Visuals to Show
- Medallion architecture diagram.
- Synthetic promotion generation logic.
- Survival curves for discounted vs non-discounted cohorts.
- Cohort heatmap by discount tier.
- LTV/CAC trend or comparison chart.
- Executive dashboard screenshot.

## Likely Questions from the Panel
- Why was synthetic data augmentation used?
- Why survival analysis instead of only classification?
- How were quality checks enforced?
- How do you prevent metric drift between teams?
- What are the limitations of the study?

## Strong Defense Points
- The project is end-to-end and reproducible.
- The business rules are explicit and traceable.
- The pipeline demonstrates engineering rigor, not just analytics.
- The study addresses a real management problem.

## Closing Statement
This project shows how a governed analytics platform can help a SaaS business move from growth at all costs to profitable growth with measurable unit economics discipline.
