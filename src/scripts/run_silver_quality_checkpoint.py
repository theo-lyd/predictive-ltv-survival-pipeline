"""Run Great Expectations checkpoint for Silver integrity constraints."""

from __future__ import annotations

import argparse
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
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = run_silver_ge_checkpoint(data_root=args.data_root, output_path=args.output)
    print(f"Silver GE checkpoint success={report['success']}")
    print(f"Validation artifact written to {args.output}")


if __name__ == "__main__":
    main()
