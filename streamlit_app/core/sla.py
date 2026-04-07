"""SLA compliance helpers for Batch 4 monitoring and dashboarding."""

from __future__ import annotations

import json
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

SLA_HISTORY_PATH = Path(__file__).resolve().parents[2] / "logs" / "sla_history.jsonl"


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

    target_path = history_path or SLA_HISTORY_PATH
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

    candidate_paths = [history_path or SLA_HISTORY_PATH]
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
