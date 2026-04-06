#!/usr/bin/env bash
set -euo pipefail

echo "[post-create] Installing Python dependencies"
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "[post-create] Done"
