"""Monitor SLA compliance and emit alert/ticket payloads for Phase 6 Batch 4."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error, request

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from streamlit_app.core.sla import (
    append_sla_history,
    build_alert_payload,
    build_compliance_audit_artifact,
    build_sla_report,
    get_compliance_audit_path,
    get_integrity_manifest_path,
    get_sla_history_path,
    get_sla_report_path,
    load_sla_history,
    summarize_report,
    write_integrity_manifest,
)


def _post_json(url: str, payload: dict[str, Any], timeout: float = 10.0, retries: int = 2) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with request.urlopen(
                req, timeout=timeout
            ) as response:  # nosec: B310 - optional webhook call
                response.read()
            return
        except (error.HTTPError, error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt >= retries:
                break
            time.sleep(2**attempt)

    if last_error is not None:
        raise last_error


def dispatch_alerts(
    report: dict[str, Any],
    dry_run: bool = True,
    webhook_url: str | None = None,
    max_retries: int = 2,
) -> list[dict[str, Any]]:
    """Prepare alert payloads and optionally send them to configured endpoints."""

    payloads = [build_alert_payload(report, item) for item in report["breaches"]]
    if dry_run or not payloads:
        return payloads

    slack_webhook_url = webhook_url or os.getenv("SLA_SLACK_WEBHOOK_URL")
    if slack_webhook_url:
        for payload in payloads:
            _post_json(slack_webhook_url, payload, retries=max_retries)

    return payloads


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Monitor SLA compliance for Phase 6 Batch 4")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text summary")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when one or more SLA breaches are detected",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=get_sla_report_path(),
        help="Write the report JSON to a file for downstream automation",
    )
    parser.add_argument(
        "--history-file",
        type=Path,
        default=get_sla_history_path(),
        help="Append a compact record to a local or archived SLA history file",
    )
    parser.add_argument(
        "--audit-output",
        type=Path,
        default=get_compliance_audit_path(),
        help="Optional compliance audit artifact output path (JSON)",
    )
    parser.add_argument(
        "--integrity-output",
        type=Path,
        default=get_integrity_manifest_path(),
        help="Integrity manifest output path (JSON)",
    )
    parser.add_argument(
        "--dispatch-alerts",
        action="store_true",
        help="Dispatch alert payloads to configured webhook endpoint",
    )
    parser.add_argument(
        "--webhook-url",
        help="Optional override for alert webhook URL",
    )
    parser.add_argument(
        "--max-dispatch-retries",
        type=int,
        default=2,
        help="Retry attempts for alert webhook delivery",
    )
    args = parser.parse_args(argv)

    report = build_sla_report()
    payloads = dispatch_alerts(
        report,
        dry_run=not args.dispatch_alerts,
        webhook_url=args.webhook_url,
        max_retries=max(args.max_dispatch_retries, 0),
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    history_target = (
        append_sla_history(report, args.history_file)
        if args.history_file
        else append_sla_history(report)
    )

    history_rows = load_sla_history(history_target)
    audit_artifact = build_compliance_audit_artifact(report=report, history=history_rows)
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.write_text(json.dumps(audit_artifact, indent=2), encoding="utf-8")

    integrity_manifest = write_integrity_manifest(
        [args.output, history_target, args.audit_output],
        output_path=args.integrity_output,
    )

    if args.json:
        print(
            json.dumps(
                {
                    "report": report,
                    "alerts": payloads,
                    "audit_output": str(args.audit_output) if args.audit_output else None,
                    "integrity_output": str(integrity_manifest),
                    "audit_artifact": audit_artifact,
                },
                indent=2,
            )
        )
    else:
        print(summarize_report(report))
        if payloads:
            print("\nAlert payloads:")
            for payload in payloads:
                print(json.dumps(payload, indent=2))

    if args.strict and report["alert_count"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
