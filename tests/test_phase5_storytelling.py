from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "airflow") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "airflow"))
if str(REPO_ROOT / "airflow" / "plugins") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "airflow" / "plugins"))

from streamlit_app.core.data_access import build_kpis, load_dashboard_data
from streamlit_app.core.narrative import load_daily_summary
from streamlit_app.core.simulator import simulate_nrr_impact
from utils.executive_storytelling import _fallback_summary


def test_simulator_monotonic_for_elasticity():
    base = 1.05
    low = simulate_nrr_impact(base, discount_percent=5, elasticity=0.8)
    high = simulate_nrr_impact(base, discount_percent=10, elasticity=0.8)
    assert high >= low


def test_kpis_return_expected_keys():
    data = load_dashboard_data()
    kpis = build_kpis(data)
    assert {"nrr", "ltv_cac", "churn_rate", "discount_efficiency"}.issubset(kpis.keys())


def test_fallback_summary_has_required_sections():
    summary = _fallback_summary({"summary": {"healthy_layers": 3, "degraded_layers": 0}}, {"churn_rate": 0.05, "invoice_count": 10, "active_customers": 25})
    assert "headline" in summary
    assert len(summary["insights"]) >= 1
    assert len(summary["actions"]) >= 1


def test_narrative_loader_fallback_shape():
    result = load_daily_summary()
    assert "headline" in result
    assert "insights" in result
    assert "actions" in result
