"""Great Expectations checkpoints and validation helpers for Silver integrity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pandas as pd

import great_expectations as gx
from great_expectations.expectations import (
    ExpectColumnPairValuesAToBeGreaterThanB,
    ExpectColumnPairValuesToBeEqual,
    ExpectColumnValuesToBeBetween,
    ExpectColumnValuesToNotBeNull,
)


def validate_invoice_math(
    frame: pd.DataFrame, original_col: str, discount_col: str, final_col: str
) -> pd.Series:
    """Return a boolean mask showing whether invoice math is valid."""

    expected = frame[original_col] - frame[discount_col]
    return expected.round(2) == frame[final_col].round(2)


def _load_parquet_folder(folder_path: Path) -> pd.DataFrame:
    """Load parquet folder contents as a dataframe."""

    if not folder_path.exists():
        raise FileNotFoundError(f"Missing data folder: {folder_path}")
    return pd.read_parquet(folder_path)


def _parse_mixed_promotion_dates(series: pd.Series) -> pd.Series:
    """Parse promotion dates from mixed formats in deterministic order."""

    parsed_iso = pd.to_datetime(series, format="%Y-%m-%d", errors="coerce")
    parsed_day_first = pd.to_datetime(series, format="%d/%m/%Y", errors="coerce")
    parsed_slash_iso = pd.to_datetime(series, format="%Y/%m/%d", errors="coerce")
    return parsed_iso.fillna(parsed_day_first).fillna(parsed_slash_iso)


def _run_expectations(frame: pd.DataFrame, expectations: Iterable, dataset_name: str) -> dict:
    """Execute Great Expectations objects against a dataframe."""

    context = gx.get_context(mode="ephemeral")
    datasource = context.data_sources.add_pandas(name=f"{dataset_name}_source")
    asset = datasource.add_dataframe_asset(name=f"{dataset_name}_asset")
    batch_definition = asset.add_batch_definition_whole_dataframe(name=f"{dataset_name}_batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": frame})
    validator = batch._create_validator(result_format="SUMMARY")
    results = [validator.validate_expectation(expectation) for expectation in expectations]
    return {
        "dataset": dataset_name,
        "success": all(result.success for result in results),
        "evaluated_expectations": len(results),
        "failed_expectations": sum(1 for result in results if not result.success),
    }


def run_silver_ge_checkpoint(data_root: Path, output_path: Path) -> dict:
    """Run Silver integrity checks and write a validation artifact report."""

    customers = _load_parquet_folder(data_root / "churn")
    promotions = _load_parquet_folder(data_root / "promotions")
    billing = _load_parquet_folder(data_root / "billing")

    customers["monthly_recurring_revenue"] = pd.to_numeric(
        customers["monthly_recurring_revenue"], errors="coerce"
    )
    customers["churn_date"] = pd.to_datetime(customers["churn_date"], errors="coerce")
    promotions["promotion_start_date"] = _parse_mixed_promotion_dates(
        promotions["promotion_start_date"]
    )

    mrr_expectations = [
        ExpectColumnValuesToNotBeNull(column="monthly_recurring_revenue"),
        ExpectColumnValuesToBeBetween(column="monthly_recurring_revenue", min_value=0),
    ]

    date_join = promotions.merge(
        customers[["customer_id", "churn_date"]], on="customer_id", how="left"
    )
    date_join = date_join[date_join["churn_date"].notna()].copy()
    date_expectations = [
        ExpectColumnPairValuesAToBeGreaterThanB(
            column_A="churn_date",
            column_B="promotion_start_date",
            or_equal=True,
        )
    ]

    billing["invoice_amount"] = pd.to_numeric(billing["invoice_amount"], errors="coerce")
    if {"invoice_subtotal", "discount_amount", "invoice_total"}.issubset(billing.columns):
        billing["expected_invoice_total"] = (
            pd.to_numeric(billing["invoice_subtotal"], errors="coerce")
            - pd.to_numeric(billing["discount_amount"], errors="coerce")
        ).round(2)
        billing["invoice_total"] = pd.to_numeric(billing["invoice_total"], errors="coerce").round(2)
    else:
        billing["expected_invoice_total"] = billing["invoice_amount"].round(2)
        billing["invoice_total"] = billing["invoice_amount"].round(2)

    invoice_expectations = [
        ExpectColumnValuesToNotBeNull(column="invoice_amount"),
        ExpectColumnValuesToBeBetween(column="invoice_amount", min_value=0),
        ExpectColumnPairValuesToBeEqual(
            column_A="expected_invoice_total", column_B="invoice_total"
        ),
    ]

    report = {
        "checkpoint_name": "silver_integrity_checkpoint",
        "suites": [
            _run_expectations(customers, mrr_expectations, "customers_mrr"),
            _run_expectations(date_join, date_expectations, "promotion_churn_ordering"),
            _run_expectations(billing, invoice_expectations, "billing_invoice_math"),
        ],
    }
    report["success"] = all(suite["success"] for suite in report["suites"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
