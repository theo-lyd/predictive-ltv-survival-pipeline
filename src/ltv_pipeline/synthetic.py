"""Synthetic promotion data generation for the ingestion pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Iterable
from xml.etree.ElementTree import Element, SubElement, tostring

import numpy as np
import pandas as pd
from faker import Faker


@dataclass(frozen=True)
class SyntheticPromotionConfig:
    seed: int = 42
    discount_cap: int = 50
    row_count: int = 1000
    null_every_n: int = 23
    duplicate_rows: int = 1


def _promotion_date_with_format_noise(index: int, date_value: str) -> str:
    """Emit mixed date formats to emulate heterogeneous source systems."""

    if index % 4 == 0:
        day, month, year = date_value.split("-")[2], date_value.split("-")[1], date_value.split("-")[0]
        return f"{day}/{month}/{year}"
    if index % 9 == 0:
        return date_value.replace("-", "/")
    return date_value


def _discount_bucket(tenure_months: float, rng: np.random.Generator, cap: int) -> tuple[str, float]:
    if tenure_months < 6:
        return "Deep Discount", float(rng.uniform(40, cap))
    if tenure_months < 18:
        return "Seasonal", float(rng.uniform(15, 30))
    return "Loyalty", float(rng.uniform(5, 10))


def generate_promotion_frame(customer_ids: Iterable[str], config: SyntheticPromotionConfig | None = None) -> pd.DataFrame:
    """Build a promotion dimension with intentionally imperfect records."""

    config = config or SyntheticPromotionConfig()
    rng = np.random.default_rng(config.seed)
    fake = Faker()
    Faker.seed(config.seed)

    customer_ids = list(customer_ids)
    if not customer_ids:
        customer_ids = [f"CUST-{idx:05d}" for idx in range(config.row_count)]

    sample_size = min(config.row_count, len(customer_ids))
    sampled_ids = rng.choice(customer_ids, size=sample_size, replace=True)
    tenures = rng.normal(loc=14, scale=8, size=sample_size).clip(min=0)

    rows = []
    for index, (customer_id, tenure_months) in enumerate(zip(sampled_ids, tenures, strict=True), start=1):
        discount_type, discount_percent = _discount_bucket(float(tenure_months), rng, config.discount_cap)
        if index % config.null_every_n == 0:
            discount_percent = np.nan
        promotion_date = fake.date_this_decade().strftime("%Y-%m-%d")
        rows.append(
            {
                "promotion_id": f"PR-{index:06d}",
                "customer_id": customer_id,
                "tenure_months": round(float(tenure_months), 2),
                "discount_type": discount_type,
                "discount_percent": round(float(discount_percent), 2) if pd.notna(discount_percent) else None,
                "promotion_start_date": _promotion_date_with_format_noise(index, promotion_date),
                "promotion_channel": rng.choice(["email", "sales", "partner", "web"]),
                "source_system": "synthetic",
            }
        )

    frame = pd.DataFrame(rows)

    if len(frame) > 3 and config.duplicate_rows > 0:
        frame = pd.concat([frame, frame.iloc[: config.duplicate_rows]], ignore_index=True)

    return frame


def write_promotion_payload(output_path: str | Path, customer_ids: Iterable[str], config: SyntheticPromotionConfig | None = None) -> Path:
    """Persist the synthetic promotion dataset as a Parquet file."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = generate_promotion_frame(customer_ids=customer_ids, config=config)
    frame.to_parquet(output_path, index=False)
    return output_path


def write_promotion_xml(output_path: str | Path, frame: pd.DataFrame) -> Path:
    """Persist promotion records as XML payload keyed by customer_id."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    root = Element("promotions")
    for record in frame.to_dict(orient="records"):
        node = SubElement(root, "promotion")
        for key, value in record.items():
            child = SubElement(node, key)
            child.text = "" if pd.isna(value) else str(value)

    output_path.write_text(tostring(root, encoding="unicode"), encoding="utf-8")
    return output_path


def write_reproducibility_report(
    output_path: str | Path,
    config: SyntheticPromotionConfig,
    row_count: int,
) -> Path:
    """Write reproducibility metadata for audit and rerun traceability."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generator": "ltv_pipeline.synthetic.generate_promotion_frame",
        "config": asdict(config),
        "generated_rows": row_count,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path
