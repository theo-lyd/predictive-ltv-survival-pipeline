"""Monitor SLA compliance and emit alert/ticket payloads for Phase 6 Batch 4."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib import request

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from streamlit_app.core.sla import append_sla_history, build_alert_payload, build_sla_report, summarize_report


def _post_json(url: str, payload: dict[str, Any], timeout: float = 10.0) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=timeout) as response:  # nosec: B310 - optional webhook call
        response.read()


def dispatch_alerts(report: dict[str, Any], dry_run: bool = True) -> list[dict[str, Any]]:
    """Prepare alert payloads and optionally send them to configured endpoints."""

    payloads = [build_alert_payload(report, item) for item in report["breaches"]]
    if dry_run or not payloads:
        return payloads

    slack_webhook_url = os.getenv("SLA_SLACK_WEBHOOK_URL")
    if slack_webhook_url:
        for payload in payloads:
            _post_json(slack_webhook_url, payload)

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
        help="Write the report JSON to a file for downstream automation",
    )
    parser.add_argument(
        "--history-file",
        type=Path,
        help="Append a compact record to a local or archived SLA history file",
    )
    args = parser.parse_args(argv)

    report = build_sla_report()
    payloads = dispatch_alerts(report, dry_run=True)

    if args.output:
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.history_file:
        append_sla_history(report, args.history_file)
    else:
        append_sla_history(report)

    if args.json:
        print(json.dumps({"report": report, "alerts": payloads}, indent=2))
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
