#!/usr/bin/env bash
set -euo pipefail

echo "[post-create] Starting environment setup at $(date)"

if ! command -v python &> /dev/null; then
  echo "[post-create] ERROR: Python not found in PATH" >&2
  exit 1
fi

echo "[post-create] Python version: $(python --version)"
echo "[post-create] Installing core dependencies from requirements.txt"

if [ ! -f "requirements.txt" ]; then
  echo "[post-create] ERROR: requirements.txt not found" >&2
  exit 1
fi

python -m pip install --upgrade --no-cache-dir pip setuptools wheel

python -m pip install --upgrade --no-cache-dir -r requirements.txt || {
  echo "[post-create] WARNING: Some dependencies may have failed to install" >&2
}

echo "[post-create] Verifying core tools"
python -m pip show dbt-databricks > /dev/null 2>&1 && echo "[post-create] dbt-databricks installed" || echo "[post-create] WARNING: dbt-databricks not found"

echo "[post-create] Environment setup complete at $(date)"
