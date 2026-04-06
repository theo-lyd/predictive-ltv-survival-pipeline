.PHONY: help install install-dev lint format test clean bootstrap validate phase1-generate phase1-ingest

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
	python -m pip install --upgrade pip
	pip install -r requirements.txt

install-dev:
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

lint:
	pylint src/ --disable=C0111,C0103 || true
	flake8 src/ --max-line-length=100 || true
	black src/ --check 2>/dev/null || true

format:
	black src/ tests/ --line-length=100
	python -m isort src/ tests/ --profile black

test:
	python -m pytest tests/ -v --cov=src --cov-report=html

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete || true
	rm -rf .coverage htmlcov/ .pytest_cache/ build/ dist/ *.egg-info

bootstrap:
	@bash scripts/bootstrap.sh

validate:
	@python tests/test_environment.py

dbt-debug:
	dbt debug --project-dir . --profiles-dir ~/.dbt

phase1-generate:
	/workspaces/predictive-ltv-survival-pipeline/.venv/bin/python src/scripts/generate_synthetic_metadata.py --row-count 1000 --seed 42

phase1-ingest:
	/workspaces/predictive-ltv-survival-pipeline/.venv/bin/python src/scripts/run_bronze_ingest.py --airbyte-enabled

.DEFAULT_GOAL := help
