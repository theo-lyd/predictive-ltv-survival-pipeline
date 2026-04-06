"""CLI entry point for generating synthetic promotion metadata."""

from __future__ import annotations

import argparse
from pathlib import Path

from ltv_pipeline.synthetic import SyntheticPromotionConfig, write_promotion_payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic promotion metadata for the thesis scaffold")
    parser.add_argument("--output", type=Path, default=Path("data/raw/promotions.parquet"))
    parser.add_argument("--row-count", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = SyntheticPromotionConfig(seed=args.seed, row_count=args.row_count)
    customer_ids = [f"CUST-{idx:05d}" for idx in range(args.row_count)]
    output = write_promotion_payload(args.output, customer_ids=customer_ids, config=config)
    print(f"Synthetic promotion metadata written to {output}")


if __name__ == "__main__":
    main()
