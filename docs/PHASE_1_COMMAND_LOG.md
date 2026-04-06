# Phase 1 Command Log: Ingestion and Bronze Layer

## Environment Setup

```bash
# Configure Python environment
/workspaces/predictive-ltv-survival-pipeline/.venv/bin/python -m pip install --upgrade pip
/workspaces/predictive-ltv-survival-pipeline/.venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
```

## Synthetic Promotions Generation

```bash
# Generate deterministic synthetic promotions with defects
/workspaces/predictive-ltv-survival-pipeline/.venv/bin/python src/scripts/generate_synthetic_metadata.py \
  --row-count 100 \
  --seed 42 \
  --discount-cap 50 \
  --null-every-n 23 \
  --duplicate-rows 1
```

Expected outputs:
- data/raw/promotions/promotions.parquet
- data/raw/promotions/promotions.xml
- data/bronze/audit/synthetic_reproducibility.json

## Bronze Ingestion

```bash
# Ingest churn + promotions + billing
/workspaces/predictive-ltv-survival-pipeline/.venv/bin/python src/scripts/run_bronze_ingest.py --airbyte-enabled

# Optional parameters
/workspaces/predictive-ltv-survival-pipeline/.venv/bin/python src/scripts/run_bronze_ingest.py \
  --header-skip 2 \
  --airbyte-enabled

# Force parquet when Delta runtime is unavailable
/workspaces/predictive-ltv-survival-pipeline/.venv/bin/python src/scripts/run_bronze_ingest.py \
  --airbyte-enabled \
  --parquet-only
```

Expected outputs:
- data/bronze/churn/*
- data/bronze/promotions/*
- data/bronze/billing/*
- data/bronze/audit/ingestion_run_<run_id>.json
- data/bronze/audit/row_count_reconciliation.csv

## Validation Commands

```bash
# Unit validation for generator and ingestion utilities
/workspaces/predictive-ltv-survival-pipeline/.venv/bin/python -m pytest tests/test_phase1_ingestion.py -v

# dbt source parse check
dbt parse
```

## Make Targets

```bash
make phase1-generate
make phase1-ingest
```

## Why-Oriented Operational Notes

- Why Spark for ingest:
  - Maintains alignment with Databricks runtime semantics and append-only table writes.
- Why append-only in Bronze:
  - Prevents destructive mutation and preserves replayable historical state.
- Why format fallbacks and normalization:
  - Real-world source feeds often include mixed encodings and abbreviated numerics.
