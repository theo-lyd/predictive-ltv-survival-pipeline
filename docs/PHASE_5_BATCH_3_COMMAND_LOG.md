# Phase 5 Batch 3 Command Log

```bash
# Run storytelling and hardening tests
python -m pytest -q tests/test_phase5_storytelling.py
python -m pytest -q tests/test_phase4_batch5_hardening.py

# Run latency validation script
python scripts/validate_phase5_dashboard_latency.py

# (Optional) Streamlit local run
streamlit run streamlit_app/app.py
```
