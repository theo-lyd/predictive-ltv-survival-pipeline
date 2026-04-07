.PHONY: help install install-dev lint format test clean bootstrap validate dbt-debug phase1-generate phase1-ingest phase2-ge-check \
	sec-audit dbt-test dbt-parse dbt-compile dbt-slim-test ci-local ge-validate sla-monitor actions-poll compliance-audit \
	phase7-latency phase7-recovery phase7-reprocess lock-deps lock-check verify-integrity

PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python; fi)
PIP := $(PYTHON) -m pip

help:
	@echo "Available commands:"
	@echo ""
	@echo "Core Setup:"
	@echo "  make install           - Install core dependencies"
	@echo "  make install-dev       - Install core + dev dependencies"
	@echo "  make lock-deps         - Regenerate pinned dependency lock files"
	@echo "  make lock-check        - Verify lock files are up to date"
	@echo "  make validate          - Validate environment setup"
	@echo "  make clean             - Clean build artifacts"
	@echo ""
	@echo "Code Quality & Linting:"
	@echo "  make lint              - Run linting checks (pylint, flake8, black)"
	@echo "  make format            - Format code with black and isort"
	@echo "  make sec-audit         - Security scanning (bandit, pip-audit)"
	@echo ""
	@echo "Testing & Validation:"
	@echo "  make test              - Run unit/integration tests with coverage"
	@echo "  make ge-validate       - Run Great Expectations quality checkpoint"
	@echo ""
	@echo "dbt Commands:"
	@echo "  make dbt-debug         - Test dbt connection"
	@echo "  make dbt-parse         - Parse dbt models (validate syntax)"
	@echo "  make dbt-compile       - Compile dbt models"
	@echo "  make dbt-test          - Run full dbt test suite"
	@echo "  make dbt-slim-test     - Run slim dbt tests (modified only)"
	@echo "  make sla-monitor       - Run SLA compliance monitor"
	@echo "  make compliance-audit  - Export structured SLA compliance artifact"
	@echo "  make phase7-latency    - Validate Phase 7 monitoring latency budgets"
	@echo "  make phase7-recovery   - Run Phase 7 recovery checks"
	@echo "  make phase7-reprocess  - Rebuild SLA history and audit artifacts"
	@echo "  make actions-poll      - Poll recent GitHub Actions runs (token required)"
	@echo ""
	@echo "CI Pipeline:"
	@echo "  make ci-local          - Run complete CI pipeline locally"
	@echo ""
	@echo "Data Pipeline:"
	@echo "  make phase1-generate   - Generate synthetic promotions payloads"
	@echo "  make phase1-ingest     - Ingest raw churn/promotions/billing into Bronze"
	@echo "  make phase2-ge-check   - Run Silver Great Expectations checkpoint"

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-lock.txt

install-dev:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-lock.txt
	$(PIP) install -r requirements-dev-lock.txt

lock-deps:
	$(PIP) install pip-tools
	$(PYTHON) -m piptools compile --no-strip-extras --no-header requirements.txt --output-file requirements-lock.txt
	$(PYTHON) -m piptools compile --no-strip-extras --no-header requirements-dev.txt --output-file requirements-dev-lock.txt

lock-check:
	$(PIP) install pip-tools
	$(PYTHON) -m piptools compile --no-strip-extras --no-header requirements.txt --output-file requirements-lock.check.txt
	$(PYTHON) -m piptools compile --no-strip-extras --no-header requirements-dev.txt --output-file requirements-dev-lock.check.txt
	diff -u requirements-lock.txt requirements-lock.check.txt
	diff -u requirements-dev-lock.txt requirements-dev-lock.check.txt
	rm -f requirements-lock.check.txt requirements-dev-lock.check.txt

lint:
	$(PYTHON) -m pylint src/ --disable=C0111,C0103,C0301,C0413,W0718,R0914,R0911,W0212
	$(PYTHON) -m flake8 src tests streamlit_app --max-line-length=100 --extend-ignore=E501,E402
	$(PYTHON) -m black src tests streamlit_app --line-length=100 --target-version=py310 --check

format:
	$(PYTHON) -m black src tests streamlit_app --line-length=100 --target-version=py310
	$(PYTHON) -m isort src tests streamlit_app --profile black

test:
	$(PYTHON) -m pytest tests -v --cov=src --cov=streamlit_app --cov-report=xml --cov-report=html --cov-report=term

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete || true
	rm -rf .coverage htmlcov/ .pytest_cache/ build/ dist/ *.egg-info

bootstrap:
	@bash scripts/bootstrap.sh

validate:
	@$(PYTHON) tests/test_environment.py

dbt-debug:
	DBT_PROFILES_DIR=$$(pwd) $(PYTHON) -m dbt debug --project-dir .

phase1-generate:
	$(PYTHON) src/scripts/generate_synthetic_metadata.py --row-count 1000 --seed 42

phase1-ingest:
	$(PYTHON) src/scripts/run_bronze_ingest.py --airbyte-enabled

phase2-ge-check:
	$(PYTHON) src/scripts/run_silver_quality_checkpoint.py

# Security & Audit commands
sec-audit:
	@echo "Running security audit..."
	$(PYTHON) -m bandit -r src streamlit_app -ll || true
	pip-audit --skip-editable --desc || true

# dbt commands
dbt-parse:
	DBT_PROFILES_DIR=$$(pwd) dbt parse --project-dir . 2>&1 | tail -20

dbt-compile:
	DBT_PROFILES_DIR=$$(pwd) dbt compile --project-dir . 2>&1 | tail -50

dbt-test:
	DBT_PROFILES_DIR=$$(pwd) dbt test --project-dir . 2>&1

dbt-slim-test:
	DBT_PROFILES_DIR=$$(pwd) dbt test --project-dir . --select state:modified --state target/ 2>&1 || true

# Data quality validation
ge-validate:
	$(PYTHON) src/scripts/run_silver_quality_checkpoint.py

# SLA monitoring
sla-monitor:
	SLA_ARTIFACTS_DIR=$${SLA_ARTIFACTS_DIR:-$$(pwd)/artifacts/sla} \
	$(PYTHON) scripts/monitor_sla_compliance.py --strict

actions-poll:
	$(PYTHON) scripts/poll_workflow_runs.py --limit 10

compliance-audit:
	SLA_ARTIFACTS_DIR=$${SLA_ARTIFACTS_DIR:-$$(pwd)/artifacts/sla} \
	$(PYTHON) scripts/export_compliance_audit.py

phase7-latency:
	$(PYTHON) scripts/validate_phase7_monitoring_latency.py

phase7-recovery:
	SLA_ARTIFACTS_DIR=$${SLA_ARTIFACTS_DIR:-$$(pwd)/artifacts/sla} $(PYTHON) -m streamlit cache clear
	SLA_ARTIFACTS_DIR=$${SLA_ARTIFACTS_DIR:-$$(pwd)/artifacts/sla} \
	$(PYTHON) scripts/monitor_sla_compliance.py --strict
	SLA_ARTIFACTS_DIR=$${SLA_ARTIFACTS_DIR:-$$(pwd)/artifacts/sla} \
	$(PYTHON) scripts/export_compliance_audit.py

phase7-reprocess:
	SLA_ARTIFACTS_DIR=$${SLA_ARTIFACTS_DIR:-$$(pwd)/artifacts/sla} \
	$(PYTHON) scripts/monitor_sla_compliance.py --strict
	SLA_ARTIFACTS_DIR=$${SLA_ARTIFACTS_DIR:-$$(pwd)/artifacts/sla} \
	$(PYTHON) scripts/export_operational_snapshot.py
	SLA_ARTIFACTS_DIR=$${SLA_ARTIFACTS_DIR:-$$(pwd)/artifacts/sla} \
	$(PYTHON) scripts/export_compliance_audit.py

verify-integrity:
	SLA_ARTIFACTS_DIR=$${SLA_ARTIFACTS_DIR:-$$(pwd)/artifacts/sla} \
	$(PYTHON) scripts/verify_integrity_manifest.py

# Complete local CI pipeline
ci-local: clean install-dev lint test dbt-parse dbt-test ge-validate
	@echo "✅ All local CI checks passed!"

.DEFAULT_GOAL := help
