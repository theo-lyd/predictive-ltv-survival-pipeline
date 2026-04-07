from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from streamlit_app.core.data_access import DashboardData
from streamlit_app.core.sla import append_sla_history, build_alert_payload, build_sla_report, load_sla_history, summarize_report


def _complete_dashboard_data() -> DashboardData:
    billing = pd.DataFrame(
        {
            "customer_id": ["c1", "c2"],
            "invoice_date": pd.to_datetime(["2026-04-01", "2026-04-02"]),
            "invoice_amount": [100.0, 120.0],
        }
    )
    churn = pd.DataFrame(
        {
            "customer_id": ["c1", "c2"],
            "signup_date": pd.to_datetime(["2025-01-01", "2025-02-01"]),
            "churn_date": pd.to_datetime([None, None]),
            "region": ["EU", "EU"],
            "product_tier": ["Pro", "Pro"],
            "monthly_recurring_revenue": [100.0, 120.0],
        }
    )
    promotions = pd.DataFrame(
        {
            "customer_id": ["c1", "c2"],
            "promotion_start_date": pd.to_datetime(["2026-03-01", "2026-03-15"]),
            "discount_percent": [5.0, 10.0],
        }
    )
    return DashboardData(
        billing=billing,
        churn=churn,
        promotions=promotions,
        source_layer="gold",
        snapshot_ts=1_800_000_000.0,
    )


def test_build_sla_report_passes_for_complete_fresh_data(monkeypatch):
    now = datetime(2026, 4, 7, 12, 0, tzinfo=timezone.utc)
    dashboard_data = _complete_dashboard_data()
    summary = {
        "summary_date": "2026-04-07",
        "headline": "All good",
        "insights": ["Fresh data."],
        "actions": ["Continue monitoring."],
        "provenance": "dbt",
        "contract_valid": True,
        "contract_errors": [],
    }

    monkeypatch.setattr("streamlit_app.core.sla.dashboard_snapshot_timestamp", lambda: now.timestamp() - 3600)
    monkeypatch.setattr("streamlit_app.core.sla.narrative_snapshot_timestamp", lambda: now.timestamp() - 1800)

    report = build_sla_report(dashboard_data=dashboard_data, narrative_summary=summary, now=now)

    assert report["alert_count"] == 0
    assert report["contract_valid"] is True
    assert report["overall_score"] >= 90
    assert all(item["status"] == "PASS" for item in report["items"])
    summary_text = summarize_report(report)
    assert "Overall score" in summary_text
    assert "Breaches: 0" in summary_text


def test_build_sla_report_detects_breaches_and_builds_payload(monkeypatch):
    now = datetime(2026, 4, 7, 12, 0, tzinfo=timezone.utc)
    dashboard_data = DashboardData(
        billing=pd.DataFrame(),
        churn=pd.DataFrame(),
        promotions=pd.DataFrame(),
        source_layer="raw-fallback",
        snapshot_ts=0.0,
    )
    summary = {
        "summary_date": "2026-04-07",
        "headline": "Fallback narrative",
        "insights": ["Missing signals."],
        "actions": ["Investigate."],
        "provenance": "fallback-template",
        "contract_valid": False,
        "contract_errors": ["missing:summary_date"],
    }

    monkeypatch.setattr("streamlit_app.core.sla.dashboard_snapshot_timestamp", lambda: 0.0)
    monkeypatch.setattr("streamlit_app.core.sla.narrative_snapshot_timestamp", lambda: 0.0)

    report = build_sla_report(dashboard_data=dashboard_data, narrative_summary=summary, now=now)

    assert report["alert_count"] >= 2
    assert any(item["status"] == "FAIL" for item in report["items"])

    first_breach = report["breaches"][0]
    payload = build_alert_payload(report, first_breach)
    assert payload["severity"] in {"P1", "P2", "P3"}
    assert payload["ticket"]["summary"]
    assert payload["ticket"]["description"]


def test_fallback_snapshot_stays_quiet_when_fresh_and_complete(monkeypatch):
    now = datetime(2026, 4, 7, 12, 0, tzinfo=timezone.utc)
    dashboard_data = _complete_dashboard_data()
    dashboard_data = DashboardData(
        billing=dashboard_data.billing,
        churn=dashboard_data.churn,
        promotions=dashboard_data.promotions,
        source_layer="raw-fallback",
        snapshot_ts=now.timestamp() - 5 * 3600,
    )
    summary = {
        "summary_date": "2026-04-07",
        "headline": "Fallback but healthy",
        "insights": ["Data is fresh."],
        "actions": ["Continue monitoring."],
        "provenance": "fallback-template",
        "contract_valid": True,
        "contract_errors": [],
    }

    monkeypatch.setattr("streamlit_app.core.sla.dashboard_snapshot_timestamp", lambda: now.timestamp() - 5 * 3600)
    monkeypatch.setattr("streamlit_app.core.sla.narrative_snapshot_timestamp", lambda: now.timestamp() - 2 * 3600)

    report = build_sla_report(dashboard_data=dashboard_data, narrative_summary=summary, now=now)

    assert report["alert_count"] == 0
    assert report["warnings"] == []
    assert all(item["status"] == "PASS" for item in report["items"])


def test_sla_history_append_and_load(tmp_path):
    now = datetime(2026, 4, 7, 12, 0, tzinfo=timezone.utc)
    dashboard_data = _complete_dashboard_data()
    summary = {
        "summary_date": "2026-04-07",
        "headline": "History test",
        "insights": ["Stable."],
        "actions": ["Keep going."],
        "provenance": "dbt",
        "contract_valid": True,
        "contract_errors": [],
    }
    report = build_sla_report(dashboard_data=dashboard_data, narrative_summary=summary, now=now)
    history_path = tmp_path / "sla_history.jsonl"

    append_sla_history(report, history_path)
    records = load_sla_history(history_path)

    assert len(records) == len(report["items"])
    assert {record["layer"] for record in records} == {item["layer"] for item in report["items"]}
    assert all(record["overall_score"] == report["overall_score"] for record in records)
