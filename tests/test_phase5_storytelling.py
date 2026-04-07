from __future__ import annotations

import sys
import types
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "airflow") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "airflow"))
if str(REPO_ROOT / "airflow" / "plugins") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "airflow" / "plugins"))

if "airflow.exceptions" not in sys.modules:
    airflow_exceptions = types.ModuleType("airflow.exceptions")

    class AirflowException(Exception):
        pass

    airflow_exceptions.AirflowException = AirflowException
    sys.modules["airflow.exceptions"] = airflow_exceptions

import pandas as pd

from streamlit_app.core.data_access import (
    DashboardData,
    apply_global_filters,
    build_kpis,
    dashboard_snapshot_timestamp,
    load_dashboard_data,
)
from streamlit_app.core.narrative import (
    _fallback_summary,
    load_daily_summary,
    narrative_snapshot_timestamp,
    validate_narrative_contract,
)
from streamlit_app.core.simulator import simulate_nrr_impact


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
    summary = _fallback_summary()
    assert "headline" in summary
    assert len(summary["insights"]) >= 1
    assert len(summary["actions"]) >= 1


def test_narrative_loader_fallback_shape():
    result = load_daily_summary()
    assert "headline" in result
    assert "insights" in result
    assert "actions" in result
    assert "contract_valid" in result
    assert "contract_errors" in result


def test_apply_global_filters_respects_date_range():
    churn = pd.DataFrame(
        {
            "customer_id": ["c1", "c2"],
            "signup_date": pd.to_datetime(["2024-01-01", "2024-05-01"]),
            "churn_date": pd.to_datetime([None, None]),
            "region": ["EU", "EU"],
            "product_tier": ["Pro", "Pro"],
            "monthly_recurring_revenue": [100.0, 200.0],
        }
    )
    billing = pd.DataFrame(
        {
            "customer_id": ["c1", "c2"],
            "invoice_date": pd.to_datetime(["2024-01-15", "2024-05-15"]),
            "invoice_amount": [100.0, 200.0],
        }
    )
    promotions = pd.DataFrame(
        {
            "customer_id": ["c1", "c2"],
            "promotion_start_date": pd.to_datetime(["2024-01-10", "2024-05-10"]),
            "discount_percent": [5.0, 10.0],
        }
    )

    filtered = apply_global_filters(
        DashboardData(billing=billing, churn=churn, promotions=promotions),
        region="EU",
        product_tier="Pro",
        date_range=(pd.Timestamp("2024-01-01"), pd.Timestamp("2024-03-31")),
    )

    assert len(filtered.churn) == 1
    assert len(filtered.billing) == 1
    assert len(filtered.promotions) == 1


def test_dashboard_data_has_provenance_and_snapshot_timestamp():
    data = load_dashboard_data()
    assert data.source_layer in {"gold", "raw-fallback"}
    assert isinstance(data.snapshot_ts, float)
    assert isinstance(dashboard_snapshot_timestamp(), float)


def test_narrative_contract_validator_detects_missing_fields():
    valid, errors = validate_narrative_contract({"headline": "x"})
    assert valid is False
    assert any(e.startswith("missing:") for e in errors)


def test_narrative_snapshot_timestamp_type():
    assert isinstance(narrative_snapshot_timestamp(), float)
