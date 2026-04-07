# Phase 5 Implementation Plan: BI and AI-Supported Storytelling

## Objective
Deliver an executive flight deck that translates data products into operational decisions.

## Batch Breakdown (Scope + Chunks)

### Batch 1: Modular Dashboard Foundation
Chunks:
1. Data access + KPI computation module.
2. Shared filter/KPI ribbon components.
3. Multi-page Streamlit skeleton.
4. Core visuals: cohort heatmap, survival comparison, sankey journey, discount simulator.

### Batch 2: AI Narrative Workflow
Chunks:
1. Daily summary generator utility.
2. Optional LLM integration with deterministic fallback.
3. Airflow task integration for scheduled summary artifact generation.
4. Narrative page binding to generated artifacts.

### Batch 3: Role Views, Glossary, and Validation
Chunks:
1. Role-focused pages for RevOps, Finance, and Sales leadership.
2. KPI glossary/help page embedded in app.
3. Latency/interaction validation script.
4. Test coverage and documentation completion.

## Decision Rationale (Why)

### Choice: Streamlit multi-page architecture
- Why: fast iteration for executive analytics and role-segmented views.
- Alternatives: custom React app, BI-only tool embedding.
- Trade-off: less UI flexibility than full custom frontend, but much faster operational delivery.

### Choice: Optional LLM + deterministic fallback
- Why: keeps narrative generation resilient when API keys are unavailable.
- Alternatives: mandatory LLM dependency.
- Trade-off: fallback is less expressive but guarantees continuity.

### Choice: Airflow-generated narrative artifact
- Why: aligns narrative generation with data freshness and observability snapshots.
- Alternatives: on-demand generation in Streamlit only.
- Trade-off: requires scheduled workflow plumbing but provides stable reproducible daily briefings.
