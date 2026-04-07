from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.export_compliance_audit import export_compliance_audit
from scripts import monitor_sla_compliance
from streamlit_app.core.sla import build_compliance_audit_artifact


def _sample_report() -> dict:
    return {
        "generated_at": "2026-04-07T10:00:00+00:00",
        "overall_score": 89.5,
        "grade": "C",
        "source_layer": "gold",
        "alert_count": 1,
        "contract_valid": False,
        "breaches": [
            {
                "layer": "Bronze",
                "metric": "Data availability",
                "status": "FAIL",
                "severity": "P1",
                "owner": "Data Ingestion Lead",
                "alert_channel": "#data-platform",
                "recommended_action": "Investigate ingestion jobs.",
                "evidence": "snapshot_age=30.0h",
                "actual": "0 rows",
                "target": "At least one fresh source",
            }
        ],
        "warnings": [
            {
                "layer": "Silver",
                "metric": "Quality checkpoint",
                "status": "WARN",
                "severity": "P3",
                "owner": "Data Analyst Lead",
                "alert_channel": "#data-quality",
                "recommended_action": "Validate null ratio.",
                "evidence": "completion=82.0%",
                "actual": "completion=82.0%",
                "target": ">=95%",
            }
        ],
        "items": [],
        "ticket_count": 1,
    }


def _sample_history() -> list[dict]:
    return [
        {
            "generated_at": "2026-04-06T10:00:00+00:00",
            "layer": "Bronze",
            "status": "WARN",
            "overall_score": 91.0,
            "grade": "B",
            "source_layer": "gold",
            "alert_count": 0,
            "breach_count": 0,
            "warning_count": 1,
            "contract_valid": True,
        },
        {
            "generated_at": "2026-04-07T10:00:00+00:00",
            "layer": "Bronze",
            "status": "FAIL",
            "overall_score": 89.5,
            "grade": "C",
            "source_layer": "gold",
            "alert_count": 1,
            "breach_count": 1,
            "warning_count": 1,
            "contract_valid": False,
        },
    ]


def test_build_compliance_audit_artifact_schema_shape():
    artifact = build_compliance_audit_artifact(report=_sample_report(), history=_sample_history())

    assert artifact["schema_version"] == "1.0.0"
    assert artifact["artifact_type"] == "sla_compliance_audit"
    assert artifact["summary"]["grade"] == "C"
    assert artifact["history"]["run_count"] >= 2
    assert "trend_summary" in artifact["history"]
    assert len(artifact["evidence"]["records"]) >= 2


def test_build_compliance_audit_artifact_missing_history_fallback():
    artifact = build_compliance_audit_artifact(report=_sample_report(), history=[])

    assert artifact["history"]["run_count"] == 1
    assert artifact["history"]["row_count"] == 0
    assert artifact["summary"]["breach_count"] == 1


def test_export_compliance_audit_writes_bundle(tmp_path):
    report_file = tmp_path / "sla_report.json"
    report_file.write_text(json.dumps(_sample_report()), encoding="utf-8")

    history_file = tmp_path / "sla_history.jsonl"
    history_file.write_text(
        "\n".join(json.dumps(row) for row in _sample_history()) + "\n",
        encoding="utf-8",
    )

    output_file = tmp_path / "compliance_audit.json"
    artifact = export_compliance_audit(
        output_file, report_file=report_file, history_file=history_file
    )

    assert output_file.exists()
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["history"]["run_count"] >= 2
    assert payload["history"]["trend_summary"]["score_delta"] is not None
    assert artifact["summary"]["grade"] == "C"


def test_monitor_cli_writes_audit_artifact(tmp_path, monkeypatch):
    history_file = tmp_path / "sla_history.jsonl"
    report_file = tmp_path / "sla_report.json"
    audit_file = tmp_path / "audit.json"
    integrity_file = tmp_path / "integrity_manifest.json"

    def _fake_append(report: dict, path: Path | None = None) -> Path:
        target = path or history_file
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "\n".join(json.dumps(row) for row in _sample_history()) + "\n", encoding="utf-8"
        )
        return target

    monkeypatch.setattr(monitor_sla_compliance, "build_sla_report", lambda: _sample_report())
    monkeypatch.setattr(monitor_sla_compliance, "append_sla_history", _fake_append)

    exit_code = monitor_sla_compliance.main(
        [
            "--output",
            str(report_file),
            "--history-file",
            str(history_file),
            "--audit-output",
            str(audit_file),
            "--integrity-output",
            str(integrity_file),
            "--json",
        ]
    )

    assert exit_code == 0
    assert report_file.exists()
    assert audit_file.exists()
    assert integrity_file.exists()
    payload = json.loads(audit_file.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "sla_compliance_audit"
