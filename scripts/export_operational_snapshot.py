"""Export an operational SLA snapshot for incident review and local debugging."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from streamlit_app.core.sla import (
    build_operational_snapshot,
    build_sla_report,
    get_sla_artifacts_dir,
    load_sla_history,
)


def export_operational_snapshot(output_path: Path, history_file: Path | None = None) -> dict:
    report = build_sla_report()
    history = load_sla_history(history_file)
    snapshot = build_operational_snapshot(report=report, history=history)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return snapshot


def main(argv: list[str] | None = None) -> int:
    default_output = get_sla_artifacts_dir() / "operational_snapshot.json"

    parser = argparse.ArgumentParser(description="Export operational SLA snapshot")
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help="Output path for snapshot JSON",
    )
    parser.add_argument(
        "--history-file",
        type=Path,
        help="Optional SLA history file path (JSONL)",
    )
    args = parser.parse_args(argv)

    snapshot = export_operational_snapshot(args.output, args.history_file)
    print(
        json.dumps(
            {"output": str(args.output), "history_runs": snapshot["history_run_count"]}, indent=2
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
