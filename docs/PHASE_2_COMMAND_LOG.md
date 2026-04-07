# Phase 2 Command Log: Silver Transformations and Integrity

## Core setup and validation

```bash
# Ensure local environment
autopep8 --version || true
make install-dev

# Parse dbt project with workspace profile directory
DBT_PROFILES_DIR=$(pwd) .venv/bin/dbt parse --project-dir .
```

## Silver model and test development

```bash
# Format and lint
make format
make lint

# Run unit and quality tests
make test

# Run Great Expectations checkpoint for Silver integrity
make phase2-ge-check
```

## dbt-specific checks

```bash
# Parse only (safe for local/CI without warehouse execution)
DBT_PROFILES_DIR=$(pwd) .venv/bin/dbt parse --project-dir .

# Optional warehouse-backed checks (requires credentials and compute)
DBT_PROFILES_DIR=$(pwd) .venv/bin/dbt run --select staging intermediate
DBT_PROFILES_DIR=$(pwd) .venv/bin/dbt test --select staging intermediate
```

## Expected validation outputs

- Lint: no flake8/black/pylint failures under configured rule set.
- Tests: all pytest tests passing.
- GE: `Silver GE checkpoint success=True`.
- Artifact: `data/quality/silver_ge_validation.json`.

## Why this command structure

- Why parse in CI: validates model contracts and graph integrity without warehouse dependency.
- Why keep run/test optional: avoids false negatives when Databricks resources are intentionally not available in CI.
- Why separate GE checkpoint command: keeps semantic quality checks explicit and auditable.
