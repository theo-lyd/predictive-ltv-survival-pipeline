"""Placeholder Bronze ingestion runner for local scaffold validation."""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare Bronze-layer input locations")
    parser.add_argument("--source", type=Path, default=Path("data/raw"))
    parser.add_argument("--target", type=Path, default=Path("data/bronze"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.target.mkdir(parents=True, exist_ok=True)
    print(f"Bronze ingestion scaffold configured from {args.source} to {args.target}")


if __name__ == "__main__":
    main()
