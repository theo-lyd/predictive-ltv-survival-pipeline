"""Export a structured compliance audit artifact from SLA report and history evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from streamlit_app.core.sla import build_compliance_audit_artifact, build_sla_report, load_sla_history


def _load_report(report_file: Path | None = None) -> dict[str, Any]:
    if report_file is None:
        return build_sla_report()
    return json.loads(report_file.read_text(encoding="utf-8"))


def export_compliance_audit(
    output_path: Path,
    report_file: Path | None = None,
    history_file: Path | None = None,
) -> dict[str, Any]:
    report = _load_report(report_file)
    history = load_sla_history(history_file)
    artifact = build_compliance_audit_artifact(report=report, history=history)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export compliance audit artifact")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("logs/compliance_audit.json"),
        help="Output path for compliance audit JSON",
    )
    parser.add_argument(
        "--report-file",
        type=Path,
        help="Optional report file path (JSON). Defaults to fresh SLA report generation.",
    )
    parser.add_argument(
        "--history-file",
        type=Path,
        help="Optional SLA history file path (JSONL)",
    )
    args = parser.parse_args(argv)

    artifact = export_compliance_audit(args.output, args.report_file, args.history_file)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "run_count": artifact["history"]["run_count"],
                "grade": artifact["summary"]["grade"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
