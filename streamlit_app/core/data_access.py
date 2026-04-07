"""Data loading and transformation helpers for executive Streamlit views."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_BILLING_PATH = REPO_ROOT / "data" / "raw" / "billing" / "billing_sync.csv"
RAW_CHURN_PATH = REPO_ROOT / "data" / "raw" / "churn" / "baseline_churn.csv"
PROMOTIONS_PATH = REPO_ROOT / "data" / "raw" / "promotions" / "promotions.parquet"


def _parse_amount(v: Any) -> float:
    if pd.isna(v):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().upper().replace(",", "")
    s = s.replace(" ", "")
    s = s.replace("MIO", "M")
    s = s.replace("MN", "M")
    if s.endswith("K"):
        return float(s[:-1]) * 1000.0
    if s.endswith("M"):
        return float(s[:-1]) * 1_000_000.0
    return float(s)


@dataclass
class DashboardData:
    billing: pd.DataFrame
    churn: pd.DataFrame
    promotions: pd.DataFrame


def load_dashboard_data() -> DashboardData:
    billing = pd.read_csv(RAW_BILLING_PATH) if RAW_BILLING_PATH.exists() else pd.DataFrame()
    churn = pd.read_csv(RAW_CHURN_PATH) if RAW_CHURN_PATH.exists() else pd.DataFrame()
    promotions = pd.read_parquet(PROMOTIONS_PATH) if PROMOTIONS_PATH.exists() else pd.DataFrame()

    if not billing.empty:
        billing["invoice_date"] = pd.to_datetime(billing["invoice_date"], errors="coerce")
        billing["invoice_amount"] = billing["invoice_amount"].map(_parse_amount)

    if not churn.empty:
        churn["signup_date"] = pd.to_datetime(churn["signup_date"], errors="coerce")
        churn["churn_date"] = pd.to_datetime(churn["churn_date"], errors="coerce")
        churn["monthly_recurring_revenue"] = churn["monthly_recurring_revenue"].map(_parse_amount)
        churn["region"] = churn["region"].replace({"NaN": "Unknown"}).fillna("Unknown")
        churn["product_tier"] = churn["product_tier"].str.title().fillna("Unknown")

    if not promotions.empty:
        promotions["promotion_start_date"] = pd.to_datetime(
            promotions["promotion_start_date"], errors="coerce"
        )

    return DashboardData(billing=billing, churn=churn, promotions=promotions)


def apply_global_filters(data: DashboardData, region: str, product_tier: str) -> DashboardData:
    churn = data.churn.copy()
    billing = data.billing.copy()
    promotions = data.promotions.copy()

    if not churn.empty and region != "All":
        churn = churn[churn["region"] == region]
    if not churn.empty and product_tier != "All":
        churn = churn[churn["product_tier"] == product_tier]

    if not billing.empty and not churn.empty and "customer_id" in billing.columns:
        billing = billing[billing["customer_id"].isin(churn["customer_id"].unique())]
    if not promotions.empty and not churn.empty and "customer_id" in promotions.columns:
        promotions = promotions[promotions["customer_id"].isin(churn["customer_id"].unique())]

    return DashboardData(billing=billing, churn=churn, promotions=promotions)


def build_kpis(data: DashboardData) -> dict[str, float]:
    if data.churn.empty:
        return {
            "nrr": 1.0,
            "ltv_cac": 0.0,
            "churn_rate": 0.0,
            "discount_efficiency": 0.0,
        }

    churn_rate = float(data.churn["churn_date"].notna().mean())
    starting_mrr = float(data.churn["monthly_recurring_revenue"].sum())

    expansion = 0.0
    if not data.promotions.empty and "discount_percent" in data.promotions.columns:
        expansion = float((data.promotions["discount_percent"].clip(0, 100) / 100.0).mean() * starting_mrr * 0.08)

    lost_mrr = float(data.churn.loc[data.churn["churn_date"].notna(), "monthly_recurring_revenue"].sum())
    nrr = (starting_mrr + expansion - lost_mrr) / starting_mrr if starting_mrr > 0 else 1.0

    avg_ltv = float(data.churn["monthly_recurring_revenue"].mean() * 18)
    avg_cac = max(350.0, float(data.churn["monthly_recurring_revenue"].mean() * 0.65))
    ltv_cac = avg_ltv / avg_cac if avg_cac > 0 else 0.0

    discount_efficiency = 0.0
    if not data.promotions.empty and "discount_percent" in data.promotions.columns:
        mean_discount = float(data.promotions["discount_percent"].mean())
        discount_efficiency = ((nrr - 1.0) * 100.0 / mean_discount) if mean_discount > 0 else 0.0

    return {
        "nrr": nrr,
        "ltv_cac": ltv_cac,
        "churn_rate": churn_rate,
        "discount_efficiency": discount_efficiency,
    }


def cohort_matrix(data: DashboardData) -> pd.DataFrame:
    if data.churn.empty:
        return pd.DataFrame()

    df = data.churn.copy()
    df["cohort_month"] = df["signup_date"].dt.to_period("M").astype(str)
    today = pd.Timestamp.utcnow().tz_localize(None)
    df["end_date"] = df["churn_date"].fillna(today)
    df["tenure_months"] = ((df["end_date"] - df["signup_date"]).dt.days / 30.0).clip(lower=0)
    df["tenure_bucket"] = (np.floor(df["tenure_months"]).astype(int)).clip(upper=24)

    pivot = (
        df.groupby(["cohort_month", "tenure_bucket"]).size().unstack(fill_value=0).sort_index()
    )
    cohort_sizes = df.groupby("cohort_month").size()

    for col in pivot.columns:
        pivot[col] = pivot[col] / cohort_sizes

    return pivot.round(3)


def survival_curves(data: DashboardData) -> pd.DataFrame:
    if data.churn.empty:
        return pd.DataFrame()

    df = data.churn.copy()
    today = pd.Timestamp.utcnow().tz_localize(None)
    df["end_date"] = df["churn_date"].fillna(today)
    df["duration"] = ((df["end_date"] - df["signup_date"]).dt.days / 30.0).clip(lower=1)
    df["event"] = df["churn_date"].notna().astype(int)

    rows = []
    for segment, g in df.groupby("product_tier"):
        for month in range(1, 25):
            at_risk = (g["duration"] >= month).sum()
            churned = ((g["duration"] <= month) & (g["event"] == 1)).sum()
            surv = 1.0 if at_risk == 0 else max(0.0, 1.0 - (churned / at_risk))
            rows.append({"segment": segment, "tenure_month": month, "survival_probability": surv})

    return pd.DataFrame(rows)


def sankey_flows(data: DashboardData) -> pd.DataFrame:
    if data.churn.empty:
        return pd.DataFrame(
            [
                {"source": "Leads", "target": "Qualified", "value": 100},
                {"source": "Qualified", "target": "Won", "value": 70},
                {"source": "Won", "target": "Retained", "value": 60},
                {"source": "Won", "target": "Churned", "value": 10},
            ]
        )

    total = max(1, len(data.churn))
    won = int(total * 0.78)
    retained = int((~data.churn["churn_date"].notna()).sum())
    churned = max(0, won - retained)

    return pd.DataFrame(
        [
            {"source": "Leads", "target": "Qualified", "value": total},
            {"source": "Qualified", "target": "Won", "value": won},
            {"source": "Won", "target": "Retained", "value": retained},
            {"source": "Won", "target": "Churned", "value": churned},
        ]
    )
