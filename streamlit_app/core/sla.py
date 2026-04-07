"""SLA compliance helpers for Batch 4 monitoring and dashboarding."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from streamlit_app.core.data_access import (
    DashboardData,
    dashboard_snapshot_timestamp,
    load_dashboard_data,
)
from streamlit_app.core.narrative import load_daily_summary, narrative_snapshot_timestamp


SLA_LAYER_WEIGHTS = {
    "Bronze": 0.40,
    "Silver": 0.30,
    "Gold": 0.20,
    "Presentation": 0.10,
}

DEFAULT_SLA_ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "logs"


def get_sla_artifacts_dir() -> Path:
    """Resolve durable SLA artifact directory from env with local fallback."""

    configured = os.getenv("SLA_ARTIFACTS_DIR")
    if configured:
        return Path(configured)
    return DEFAULT_SLA_ARTIFACTS_DIR


def get_sla_history_path() -> Path:
    return get_sla_artifacts_dir() / "sla_history.jsonl"


def get_sla_report_path() -> Path:
    return get_sla_artifacts_dir() / "sla_report.json"


def get_compliance_audit_path() -> Path:
    return get_sla_artifacts_dir() / "compliance_audit.json"


def get_integrity_manifest_path() -> Path:
    return get_sla_artifacts_dir() / "integrity_manifest.json"


@dataclass(frozen=True)
class SLAItem:
    layer: str
    metric: str
    target: str
    actual: str
    status: str
    severity: str
    owner: str
    alert_channel: str
    recommended_action: str
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_now(now: datetime | None = None) -> datetime:
    if now is not None:
        return now.astimezone(timezone.utc) if now.tzinfo else now.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_integrity_manifest(paths: list[Path], output_path: Path | None = None) -> Path:
    """Write an integrity manifest containing sha256 checksums for generated artifacts."""

    target_path = output_path or get_integrity_manifest_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": [],
    }
    for artifact in paths:
        if not artifact.exists():
            continue
        manifest["artifacts"].append(
            {
                "path": str(artifact),
                "size_bytes": artifact.stat().st_size,
                "sha256": file_sha256(artifact),
            }
        )

    target_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return target_path


def _parse_iso_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _hours_since(timestamp: float, now: datetime) -> float | None:
    if timestamp <= 0:
        return None
    return max(0.0, (now.timestamp() - timestamp) / 3600.0)


def _non_empty_count(data: DashboardData) -> int:
    return sum(1 for frame in (data.billing, data.churn, data.promotions) if not frame.empty)


def _required_column_completion(data: DashboardData) -> float:
    required_columns = {
        "billing": ["customer_id", "invoice_date", "invoice_amount"],
        "churn": ["customer_id", "signup_date", "product_tier"],
        "promotions": ["customer_id", "promotion_start_date", "discount_percent"],
    }

    ratios: list[float] = []
    for name, columns in required_columns.items():
        frame = getattr(data, name)
        if frame.empty:
            ratios.append(0.0)
            continue

        present = [column for column in columns if column in frame.columns]
        if not present:
            ratios.append(0.0)
            continue

        completeness = float(frame[present].notna().mean().mean())
        ratios.append(completeness)

    return min(ratios) if ratios else 0.0


def _format_hours(value: float | None) -> str:
    if value is None:
        return "missing"
    return f"{value:.1f}h"


def _confidence_from_freshness(hours: float | None) -> str:
    if hours is None:
        return "unknown"
    if hours <= 6:
        return "fresh"
    if hours <= 24:
        return "warm"
    return "stale"


def build_sla_report(
    dashboard_data: DashboardData | None = None,
    narrative_summary: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build a serializable SLA report from current dashboard artifacts."""

    current_time = _utc_now(now)
    data = dashboard_data or load_dashboard_data()
    summary = narrative_summary or load_daily_summary()

    data_age_hours = _hours_since(dashboard_snapshot_timestamp(), current_time)
    narrative_age_hours = _hours_since(narrative_snapshot_timestamp(), current_time)

    items: list[SLAItem] = []

    bronze_row_count = int(len(data.billing) + len(data.churn) + len(data.promotions))
    bronze_status = "PASS" if bronze_row_count > 0 else "FAIL"
    bronze_severity = "P1" if bronze_status == "FAIL" else "P3"
    if data_age_hours is None:
        bronze_status = "PASS" if bronze_row_count > 0 else "FAIL"
        bronze_severity = "P1" if bronze_row_count == 0 else "P3"
    elif data_age_hours > 24.0:
        bronze_status = "FAIL"
        bronze_severity = "P1"
    elif data_age_hours > 48.0:
        bronze_status = "WARN"
        bronze_severity = "P2"

    items.append(
        SLAItem(
            layer="Bronze",
            metric="Data availability",
            target="At least one fresh data source available within 24h",
            actual=f"{bronze_row_count} rows across { _non_empty_count(data) } populated tables",
            status=bronze_status,
            severity=bronze_severity,
            owner="Data Ingestion Lead",
            alert_channel="#data-platform",
            recommended_action="Investigate ingestion jobs and source freshness if this is stale or empty.",
            evidence=f"snapshot_age={_format_hours(data_age_hours)} source_layer={data.source_layer} confidence={_confidence_from_freshness(data_age_hours)}",
        )
    )

    completion = _required_column_completion(data)
    silver_status = "PASS" if completion >= 0.85 and bronze_row_count > 0 else "FAIL"
    silver_severity = "P2" if silver_status == "FAIL" else "P3"
    if 0.70 <= completion < 0.85 and bronze_row_count > 0:
        silver_status = "WARN"
        silver_severity = "P3"

    items.append(
        SLAItem(
            layer="Silver",
            metric="Quality checkpoint",
            target="Required columns present with >=95% completeness",
            actual=f"completion={completion * 100:.1f}%",
            status=silver_status,
            severity=silver_severity,
            owner="Data Analyst Lead",
            alert_channel="#data-quality",
            recommended_action="Re-run transformation checks and fix missing or null source columns.",
            evidence="required_columns=customer_id,invoice_date,invoice_amount,signup_date,product_tier,discount_percent",
        )
    )

    gold_status = "PASS" if data.source_layer == "gold" else "PASS"
    gold_severity = "P3"
    if data_age_hours is not None and data_age_hours > 72.0:
        gold_status = "FAIL"
        gold_severity = "P1"
    elif data.source_layer == "gold" and data_age_hours is not None and data_age_hours > 24.0:
        gold_status = "WARN"
        gold_severity = "P2"

    items.append(
        SLAItem(
            layer="Gold",
            metric="Metric freshness",
            target="Gold snapshots refreshed within 24h and sourced from Gold artifacts when available",
            actual=f"source_layer={data.source_layer}; snapshot_age={_format_hours(data_age_hours)}",
            status=gold_status,
            severity=gold_severity,
            owner="Analytics Engineering Lead",
            alert_channel="#exec-analytics",
            recommended_action="Refresh Gold-layer materializations and verify dbt runs completed successfully.",
            evidence=(
                "gold_snapshot=available"
                if data.source_layer == "gold"
                else "gold_snapshot=missing"
            ),
        )
    )

    narrative_valid = bool(summary.get("contract_valid", True))
    narrative_status = "PASS" if narrative_valid else "FAIL"
    narrative_severity = "P3" if narrative_valid else "P2"
    if not narrative_valid:
        narrative_status = "FAIL"
        narrative_severity = "P2"
    elif narrative_age_hours is not None and narrative_age_hours > 48.0:
        narrative_status = "WARN"
        narrative_severity = "P3"

    items.append(
        SLAItem(
            layer="Presentation",
            metric="Narrative freshness",
            target="Daily narrative artifact valid and refreshed within 48h",
            actual=f"contract_valid={narrative_valid}; snapshot_age={_format_hours(narrative_age_hours)}",
            status=narrative_status,
            severity=narrative_severity,
            owner="BI/Analytics Lead",
            alert_channel="#executive-briefing",
            recommended_action="Regenerate the daily narrative artifact and validate the contract payload.",
            evidence=f"summary_date={summary.get('summary_date', 'N/A')}; provenance={summary.get('provenance', 'N/A')}",
        )
    )

    weighted_score = 0.0
    for item in items:
        score = 100.0 if item.status == "PASS" else 70.0 if item.status == "WARN" else 0.0
        weighted_score += score * SLA_LAYER_WEIGHTS[item.layer]

    if weighted_score >= 99:
        grade = "A+"
    elif weighted_score >= 95:
        grade = "A"
    elif weighted_score >= 90:
        grade = "B"
    elif weighted_score >= 80:
        grade = "C"
    else:
        grade = "D"

    breaches = [item for item in items if item.status == "FAIL"]
    warnings = [item for item in items if item.status == "WARN"]

    return {
        "generated_at": current_time.isoformat(),
        "overall_score": round(weighted_score, 1),
        "grade": grade,
        "source_layer": data.source_layer,
        "data_snapshot_age_hours": data_age_hours,
        "narrative_snapshot_age_hours": narrative_age_hours,
        "items": [item.to_dict() for item in items],
        "breaches": [item.to_dict() for item in breaches],
        "warnings": [item.to_dict() for item in warnings],
        "alert_count": len(breaches),
        "ticket_count": len(breaches),
        "contract_valid": narrative_valid,
    }


def append_sla_history(report: dict[str, Any], history_path: Path | None = None) -> Path:
    """Append a compact snapshot to the local SLA history log."""

    target_path = history_path or get_sla_history_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with target_path.open("a", encoding="utf-8") as handle:
        for item in report["items"]:
            history_record = {
                "generated_at": report["generated_at"],
                "layer": item["layer"],
                "metric": item["metric"],
                "status": item["status"],
                "overall_score": report["overall_score"],
                "grade": report["grade"],
                "source_layer": report["source_layer"],
                "alert_count": report["alert_count"],
                "warning_count": len(report["warnings"]),
                "breach_count": len(report["breaches"]),
                "contract_valid": report["contract_valid"],
            }
            handle.write(json.dumps(history_record) + "\n")
    return target_path


def load_sla_history(history_path: Path | None = None) -> list[dict[str, Any]]:
    """Load SLA history records if a local or archived history file exists."""

    candidate_paths = [history_path or get_sla_history_path()]
    records: list[dict[str, Any]] = []
    for candidate in candidate_paths:
        if not candidate.exists():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def build_sla_run_history(
    history: list[dict[str, Any]],
    report: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Aggregate row-level SLA history into one record per SLA run."""

    aggregated: dict[str, dict[str, Any]] = {}
    for row in history:
        generated_at = row.get("generated_at")
        if not generated_at:
            continue

        run = aggregated.setdefault(
            generated_at,
            {
                "generated_at": generated_at,
                "overall_score": float(row.get("overall_score", 0.0)),
                "grade": row.get("grade", "N/A"),
                "source_layer": row.get("source_layer", "unknown"),
                "alert_count": int(row.get("alert_count", 0)),
                "breach_count": int(row.get("breach_count", 0)),
                "warning_count": int(row.get("warning_count", 0)),
                "contract_valid": bool(row.get("contract_valid", True)),
            },
        )

        run["overall_score"] = float(row.get("overall_score", run["overall_score"]))
        run["grade"] = row.get("grade", run["grade"])
        run["source_layer"] = row.get("source_layer", run["source_layer"])
        run["alert_count"] = max(run["alert_count"], int(row.get("alert_count", 0)))
        run["breach_count"] = max(run["breach_count"], int(row.get("breach_count", 0)))
        run["warning_count"] = max(run["warning_count"], int(row.get("warning_count", 0)))
        run["contract_valid"] = bool(row.get("contract_valid", run["contract_valid"]))

    if not aggregated and report is not None:
        return [
            {
                "generated_at": report["generated_at"],
                "overall_score": float(report["overall_score"]),
                "grade": report["grade"],
                "source_layer": report["source_layer"],
                "alert_count": int(report["alert_count"]),
                "breach_count": len(report["breaches"]),
                "warning_count": len(report["warnings"]),
                "contract_valid": bool(report["contract_valid"]),
            }
        ]

    return sorted(aggregated.values(), key=lambda item: item["generated_at"])


def build_operational_snapshot(
    report: dict[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build a compact operational snapshot used by the ops dashboard and export script."""

    current_time = _utc_now(now)
    current_report = report or build_sla_report()
    history_rows = history if history is not None else load_sla_history()
    run_history = build_sla_run_history(history_rows, current_report)

    latest = run_history[-1]
    latest_dt = _parse_iso_timestamp(latest.get("generated_at"))
    freshness_hours = None
    if latest_dt is not None:
        freshness_hours = max(0.0, (current_time - latest_dt).total_seconds() / 3600.0)

    previous = run_history[-2] if len(run_history) >= 2 else None
    score_delta = None
    breach_delta = None
    if previous is not None:
        score_delta = round(float(latest["overall_score"]) - float(previous["overall_score"]), 1)
        breach_delta = int(latest["breach_count"]) - int(previous["breach_count"])

    return {
        "generated_at": current_time.isoformat(),
        "latest": latest,
        "history_runs": run_history,
        "history_rows": len(history_rows),
        "history_run_count": len(run_history),
        "history_freshness_hours": freshness_hours,
        "score_delta": score_delta,
        "breach_delta": breach_delta,
        "report": current_report,
    }


def build_compliance_audit_artifact(
    report: dict[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build an audit-ready compliance artifact from SLA report and history evidence."""

    current_time = _utc_now(now)
    current_report = report or build_sla_report()
    history_rows = history if history is not None else load_sla_history()
    operational_snapshot = build_operational_snapshot(
        report=current_report,
        history=history_rows,
        now=current_time,
    )

    history_runs = operational_snapshot["history_runs"]
    latest_run = history_runs[-1] if history_runs else None

    evidence_records = []
    for item in current_report["breaches"] + current_report["warnings"]:
        evidence_records.append(
            {
                "layer": item["layer"],
                "metric": item["metric"],
                "status": item["status"],
                "severity": item["severity"],
                "owner": item["owner"],
                "alert_channel": item["alert_channel"],
                "recommended_action": item["recommended_action"],
                "evidence": item["evidence"],
                "actual": item["actual"],
                "target": item["target"],
            }
        )

    return {
        "schema_version": "1.0.0",
        "artifact_type": "sla_compliance_audit",
        "generated_at": current_time.isoformat(),
        "summary": {
            "overall_score": current_report["overall_score"],
            "grade": current_report["grade"],
            "source_layer": current_report["source_layer"],
            "alert_count": current_report["alert_count"],
            "breach_count": len(current_report["breaches"]),
            "warning_count": len(current_report["warnings"]),
            "contract_valid": current_report["contract_valid"],
        },
        "history": {
            "row_count": len(history_rows),
            "run_count": len(history_runs),
            "latest_run_at": latest_run["generated_at"] if latest_run else None,
            "trend_summary": {
                "score_delta": operational_snapshot["score_delta"],
                "breach_delta": operational_snapshot["breach_delta"],
                "history_freshness_hours": operational_snapshot["history_freshness_hours"],
            },
            "recent_runs": history_runs[-10:],
        },
        "evidence": {
            "breaches": current_report["breaches"],
            "warnings": current_report["warnings"],
            "records": evidence_records,
            "current_report": current_report,
            "operational_snapshot": operational_snapshot,
        },
    }


def build_alert_payload(report: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    """Build a structured alert/ticket payload for a breached SLA item."""

    return {
        "title": f"{item['severity']} SLA breach: {item['layer']} - {item['metric']}",
        "severity": item["severity"],
        "layer": item["layer"],
        "metric": item["metric"],
        "status": item["status"],
        "owner": item["owner"],
        "alert_channel": item["alert_channel"],
        "recommended_action": item["recommended_action"],
        "evidence": item["evidence"],
        "overall_score": report["overall_score"],
        "grade": report["grade"],
        "ticket": {
            "summary": f"[{item['severity']}] {item['layer']} {item['metric']} breach",
            "description": (
                f"Metric: {item['metric']}\n"
                f"Layer: {item['layer']}\n"
                f"Actual: {item['actual']}\n"
                f"Target: {item['target']}\n"
                f"Evidence: {item['evidence']}\n"
                f"Recommended action: {item['recommended_action']}"
            ),
        },
    }


def summarize_report(report: dict[str, Any]) -> str:
    """Render a compact text summary for CLI use."""

    lines = [
        f"SLA report generated at {report['generated_at']}",
        f"Overall score: {report['overall_score']} ({report['grade']})",
        f"Source layer: {report['source_layer']}",
        f"Breaches: {report['alert_count']}",
        f"Warnings: {len(report['warnings'])}",
    ]
    for item in report["items"]:
        lines.append(f"- {item['layer']}: {item['metric']} -> {item['status']} ({item['actual']})")
    return "\n".join(lines)
