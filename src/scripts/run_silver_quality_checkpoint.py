"""Run Great Expectations checkpoint for Silver integrity constraints."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ltv_pipeline.quality import run_silver_ge_checkpoint


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Silver Great Expectations checkpoint")
    parser.add_argument("--data-root", type=Path, default=Path("data/bronze"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/quality/silver_ge_validation.json"),
    )
    parser.add_argument(
        "--allow-missing-data",
        action="store_true",
        help="Exit successfully with a skipped report when bronze data folders are unavailable",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        report = run_silver_ge_checkpoint(data_root=args.data_root, output_path=args.output)
    except FileNotFoundError as exc:
        if not args.allow_missing_data:
            raise

        report = {
            "checkpoint_name": "silver_integrity_checkpoint",
            "success": True,
            "skipped": True,
            "reason": str(exc),
            "suites": [],
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Silver GE checkpoint success={report['success']}")
    if report.get("skipped"):
        print(f"Silver GE checkpoint skipped: {report['reason']}")
    print(f"Validation artifact written to {args.output}")


if __name__ == "__main__":
    main()
