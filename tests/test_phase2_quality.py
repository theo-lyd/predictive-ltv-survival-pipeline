import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from ltv_pipeline.quality import run_silver_ge_checkpoint


def _write_parquet(df: pd.DataFrame, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    df.to_parquet(folder / "part-00000.parquet", index=False)


def test_silver_ge_checkpoint_passes(tmp_path: Path):
    bronze = tmp_path / "bronze"
    _write_parquet(
        pd.DataFrame(
            {
                "customer_id": ["C1", "C2"],
                "monthly_recurring_revenue": [100.0, 50.0],
                "churn_date": [None, "2024-03-31"],
            }
        ),
        bronze / "churn",
    )
    _write_parquet(
        pd.DataFrame(
            {
                "customer_id": ["C2"],
                "promotion_start_date": ["2024-01-10"],
                "invoice_amount": [10.0],
            }
        ),
        bronze / "promotions",
    )
    _write_parquet(
        pd.DataFrame(
            {
                "customer_id": ["C1"],
                "invoice_amount": [100.0],
                "invoice_subtotal": [105.0],
                "discount_amount": [5.0],
                "invoice_total": [100.0],
            }
        ),
        bronze / "billing",
    )

    out = tmp_path / "quality" / "silver_ge_validation.json"
    report = run_silver_ge_checkpoint(data_root=bronze, output_path=out)

    assert out.exists()
    assert report["success"] is True


def test_silver_ge_checkpoint_fails_negative_mrr(tmp_path: Path):
    bronze = tmp_path / "bronze"
    _write_parquet(
        pd.DataFrame(
            {
                "customer_id": ["C1"],
                "monthly_recurring_revenue": [-5.0],
                "churn_date": [None],
            }
        ),
        bronze / "churn",
    )
    _write_parquet(
        pd.DataFrame(
            {
                "customer_id": ["C1"],
                "promotion_start_date": ["2024-01-10"],
                "invoice_amount": [5.0],
            }
        ),
        bronze / "promotions",
    )
    _write_parquet(
        pd.DataFrame(
            {
                "customer_id": ["C1"],
                "invoice_amount": [5.0],
                "invoice_subtotal": [6.0],
                "discount_amount": [1.0],
                "invoice_total": [5.0],
            }
        ),
        bronze / "billing",
    )

    out = tmp_path / "quality" / "silver_ge_validation.json"
    report = run_silver_ge_checkpoint(data_root=bronze, output_path=out)

    assert report["success"] is False
