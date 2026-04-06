"""CLI entry point for generating synthetic promotion metadata."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ltv_pipeline.synthetic import (
    SyntheticPromotionConfig,
    generate_promotion_frame,
    write_promotion_xml,
    write_reproducibility_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate synthetic promotion metadata for the thesis scaffold"
    )
    parser.add_argument(
        "--parquet-output", type=Path, default=Path("data/raw/promotions/promotions.parquet")
    )
    parser.add_argument(
        "--xml-output", type=Path, default=Path("data/raw/promotions/promotions.xml")
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=Path("data/bronze/audit/synthetic_reproducibility.json"),
    )
    parser.add_argument("--row-count", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--discount-cap", type=int, default=50)
    parser.add_argument("--null-every-n", type=int, default=23)
    parser.add_argument("--duplicate-rows", type=int, default=1)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = SyntheticPromotionConfig(
        seed=args.seed,
        row_count=args.row_count,
        discount_cap=args.discount_cap,
        null_every_n=args.null_every_n,
        duplicate_rows=args.duplicate_rows,
    )
    customer_ids = [f"CUST-{idx:05d}" for idx in range(args.row_count)]
    frame = generate_promotion_frame(customer_ids=customer_ids, config=config)

    args.parquet_output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(args.parquet_output, index=False)
    write_promotion_xml(args.xml_output, frame)
    write_reproducibility_report(args.report_output, config=config, row_count=len(frame))

    print(f"Synthetic promotion Parquet written to {args.parquet_output}")
    print(f"Synthetic promotion XML written to {args.xml_output}")
    print(f"Reproducibility report written to {args.report_output}")


if __name__ == "__main__":
    main()
