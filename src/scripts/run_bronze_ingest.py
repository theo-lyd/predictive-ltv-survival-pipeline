"""Bronze ingestion runner with append-only semantics and audit logging."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType,
    StringType,
    StructField,
    StructType,
)

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ltv_pipeline.ingestion import normalize_numeric_abbrev


def _read_with_encoding_fallback(path: Path, header_skip: int) -> pd.DataFrame:
    """Read a messy CSV with UTF-8 fallback to Latin-1 and optional preamble skip."""

    last_error: Exception | None = None
    for encoding in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding, skiprows=header_skip)
        except Exception as exc:  # pragma: no cover - guarded fallback path
            last_error = exc
    raise RuntimeError(f"Failed to read {path} with UTF-8/Latin-1 encodings") from last_error


def _ensure_directories(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def _spark_write_append(df, output_path: Path, prefer_delta: bool) -> str:
    """Append data using Delta where available; fallback to Parquet for local portability."""

    if prefer_delta:
        try:
            df.write.format("delta").mode("append").save(str(output_path))
            return "delta"
        except Exception:
            pass

    df.write.format("parquet").mode("append").save(str(output_path))
    return "parquet"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest churn, promotions, and billing into Bronze append-only tables"
    )
    parser.add_argument("--source", type=Path, default=Path("data/raw"))
    parser.add_argument("--target", type=Path, default=Path("data/bronze"))
    parser.add_argument("--header-skip", type=int, default=0)
    parser.add_argument("--airbyte-enabled", action="store_true")
    parser.add_argument("--parquet-only", action="store_true")
    parser.add_argument("--run-id", type=str, default="")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    prefer_delta = not args.parquet_only

    audit_path = args.target / "audit"
    churn_path = args.target / "churn"
    promotions_path = args.target / "promotions"
    billing_path = args.target / "billing"
    _ensure_directories([args.target, audit_path, churn_path, promotions_path, billing_path])

    churn_raw = args.source / "churn" / "baseline_churn.csv"
    promotions_parquet = args.source / "promotions" / "promotions.parquet"
    billing_raw = args.source / "billing" / "billing_sync.csv"

    if not churn_raw.exists():
        raise FileNotFoundError(f"Missing baseline churn file: {churn_raw}")
    if not promotions_parquet.exists():
        raise FileNotFoundError(f"Missing promotions parquet file: {promotions_parquet}")

    spark = (
        SparkSession.builder.appName("phase1-bronze-ingest")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )

    churn_pdf = _read_with_encoding_fallback(churn_raw, header_skip=args.header_skip)
    if "monthly_recurring_revenue" in churn_pdf.columns:
        churn_pdf["monthly_recurring_revenue"] = churn_pdf["monthly_recurring_revenue"].apply(
            normalize_numeric_abbrev
        )

    churn_schema = StructType(
        [
            StructField("customer_id", StringType(), True),
            StructField("subscription_id", StringType(), True),
            StructField("signup_date", StringType(), True),
            StructField("churn_date", StringType(), True),
            StructField("region", StringType(), True),
            StructField("product_tier", StringType(), True),
            StructField("monthly_recurring_revenue", DoubleType(), True),
        ]
    )
    churn_df = (
        spark.createDataFrame(churn_pdf, schema=churn_schema)
        .withColumn("ingestion_run_id", F.lit(run_id))
        .withColumn("ingested_at_utc", F.current_timestamp())
    )

    promotions_df = (
        spark.read.parquet(str(promotions_parquet))
        .withColumn("ingestion_run_id", F.lit(run_id))
        .withColumn("ingested_at_utc", F.current_timestamp())
    )

    billing_ingested = False
    billing_count = 0
    billing_format = "not_ingested"
    if args.airbyte_enabled and billing_raw.exists():
        billing_pdf = _read_with_encoding_fallback(billing_raw, header_skip=args.header_skip)
        if "invoice_amount" in billing_pdf.columns:
            billing_pdf["invoice_amount"] = billing_pdf["invoice_amount"].apply(
                normalize_numeric_abbrev
            )
        billing_df = (
            spark.createDataFrame(billing_pdf)
            .withColumn("ingestion_run_id", F.lit(run_id))
            .withColumn("ingested_at_utc", F.current_timestamp())
        )
        billing_format = _spark_write_append(billing_df, billing_path, prefer_delta=prefer_delta)
        billing_count = billing_df.count()
        billing_ingested = True

    churn_format = _spark_write_append(churn_df, churn_path, prefer_delta=prefer_delta)
    promotions_format = _spark_write_append(
        promotions_df, promotions_path, prefer_delta=prefer_delta
    )

    record = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_root": str(args.source),
        "target_root": str(args.target),
        "header_skip": args.header_skip,
        "airbyte_enabled": args.airbyte_enabled,
        "tables": {
            "churn": {"rows_ingested": churn_df.count(), "format": churn_format},
            "promotions": {"rows_ingested": promotions_df.count(), "format": promotions_format},
            "billing": {
                "rows_ingested": billing_count,
                "format": billing_format,
                "ingested": billing_ingested,
            },
        },
    }

    audit_json = audit_path / f"ingestion_run_{run_id}.json"
    audit_json.write_text(json.dumps(record, indent=2), encoding="utf-8")

    reconciliation = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "table_name": "churn",
                "rows_ingested": record["tables"]["churn"]["rows_ingested"],
            },
            {
                "run_id": run_id,
                "table_name": "promotions",
                "rows_ingested": record["tables"]["promotions"]["rows_ingested"],
            },
            {
                "run_id": run_id,
                "table_name": "billing",
                "rows_ingested": record["tables"]["billing"]["rows_ingested"],
            },
        ]
    )
    reconciliation.to_csv(
        audit_path / "row_count_reconciliation.csv",
        mode="a",
        header=not (audit_path / "row_count_reconciliation.csv").exists(),
        index=False,
    )

    spark.stop()
    print(f"Bronze ingestion complete for run_id={run_id}")
    print(f"Audit log written to {audit_json}")


if __name__ == "__main__":
    main()
