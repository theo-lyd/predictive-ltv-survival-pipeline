"""KPI definitions for executive dashboard help and glossary views."""

KPI_GLOSSARY = {
    "Net Revenue Retention (NRR)": {
        "definition": "Revenue retained from an existing cohort after expansions, contractions, and churn.",
        "formula": "(Starting MRR + Expansion - Contraction - Churn) / Starting MRR",
        "why_it_matters": "Primary signal for durable growth quality without reliance on new logo acquisition.",
    },
    "LTV/CAC": {
        "definition": "Ratio between customer lifetime value and customer acquisition cost.",
        "formula": "Average Customer LTV / Average CAC",
        "why_it_matters": "Evaluates whether growth is capital efficient and scalable.",
    },
    "Gross Revenue Churn": {
        "definition": "Portion of recurring revenue lost due to cancellations/downgrades over a period.",
        "formula": "(Lost MRR in period) / (Opening MRR)",
        "why_it_matters": "Direct indicator of customer value realization and retention risk.",
    },
    "Discount Efficiency": {
        "definition": "Incremental retained revenue generated per 1% point of discount granted.",
        "formula": "NRR uplift / Discount percentage",
        "why_it_matters": "Prevents margin erosion from unproductive discounting behavior.",
    },
    "Survival Probability": {
        "definition": "Probability that a cohort remains active beyond a given tenure month.",
        "formula": "Kaplan-Meier survival estimate",
        "why_it_matters": "Turns retention curves into forward-looking operating decisions by segment.",
    },
}

STRATEGIC_QUESTIONS = [
    "Where are we gaining or losing retention momentum across cohorts?",
    "Which customer segments create durable NRR without margin-destructive discounting?",
    "How do survival curves differ by region, product tier, and leadership-owned segment?",
    "What discount policy shift improves NRR while protecting LTV quality?",
]
