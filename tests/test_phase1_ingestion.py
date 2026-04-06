import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from ltv_pipeline.ingestion import normalize_numeric_abbrev
from ltv_pipeline.synthetic import (
    SyntheticPromotionConfig,
    generate_promotion_frame,
    write_promotion_xml,
    write_reproducibility_report,
)


def test_numeric_normalization():
    assert normalize_numeric_abbrev("1.5K") == 1500.0
    assert normalize_numeric_abbrev("2 Mio") == 2000000.0
    assert normalize_numeric_abbrev("100") == 100.0
    assert normalize_numeric_abbrev(None) is None


def test_synthetic_generator_defects_and_policy(tmp_path: Path):
    config = SyntheticPromotionConfig(seed=7, row_count=120, null_every_n=10, duplicate_rows=2)
    customer_ids = [f"CUST-{i:05d}" for i in range(120)]
    frame = generate_promotion_frame(customer_ids=customer_ids, config=config)

    assert len(frame) >= 122
    assert frame["customer_id"].notna().all()

    null_discount_count = frame["discount_percent"].isna().sum()
    assert null_discount_count >= 10

    short_tenure = frame[frame["tenure_months"] < 6]
    assert (short_tenure["discount_type"] == "Deep Discount").all()


def test_xml_and_reproducibility_outputs(tmp_path: Path):
    config = SyntheticPromotionConfig(seed=11, row_count=25)
    customer_ids = [f"CUST-{i:05d}" for i in range(25)]
    frame = generate_promotion_frame(customer_ids=customer_ids, config=config)

    xml_path = write_promotion_xml(tmp_path / "promotions.xml", frame)
    report_path = write_reproducibility_report(
        tmp_path / "synthetic_report.json", config, row_count=len(frame)
    )

    assert xml_path.exists()
    assert report_path.exists()

    report = pd.read_json(report_path)
    assert "generated_rows" in report.columns
