.PHONY: help install install-dev lint format test clean bootstrap validate phase1-generate phase1-ingest

PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python; fi)
PIP := $(PYTHON) -m pip

help:
	@echo "Available commands:"
	@echo "  make install           - Install core dependencies"
	@echo "  make install-dev       - Install core + dev dependencies"
	@echo "  make lint              - Run linting checks"
	@echo "  make format            - Format code with black"
	@echo "  make test              - Run tests"
	@echo "  make clean             - Clean build artifacts"
	@echo "  make bootstrap         - Run project bootstrap"
	@echo "  make validate          - Validate environment setup"
	@echo "  make dbt-debug         - Test dbt connection"
	@echo "  make phase1-generate   - Generate synthetic promotions payloads"
	@echo "  make phase1-ingest     - Ingest raw churn/promotions/billing into Bronze"

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

lint:
	$(PYTHON) -m pylint src/ --disable=C0111,C0103,C0301,C0413,W0718,R0914,R0911
	$(PYTHON) -m flake8 src tests --max-line-length=100 --extend-ignore=E501,E402
	$(PYTHON) -m black src tests --line-length=100 --check

format:
	$(PYTHON) -m black src tests --line-length=100
	$(PYTHON) -m isort src tests --profile black

test:
	$(PYTHON) -m pytest tests -v --cov=src --cov-report=html

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

.DEFAULT_GOAL := help
