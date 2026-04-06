#!/usr/bin/env bash
#
# Setup Databricks secrets for the project
#
# Usage: bash scripts/setup_secrets.sh
#
# This script helps configure Databricks credentials as environment variables

set -euo pipefail

echo "Databricks Secrets Setup"
echo "========================"
echo ""
echo "Please provide your Databricks credentials:"
echo ""

read -p "Databricks Host (e.g., abc123.cloud.databricks.com): " DATABRICKS_HOST
read -p "Databricks HTTP Path (e.g., /sql/1.0/warehouses/abc123): " DATABRICKS_HTTP_PATH
read -sp "Databricks Token: " DATABRICKS_TOKEN
echo ""

# Validate inputs
if [ -z "$DATABRICKS_HOST" ] || [ -z "$DATABRICKS_HTTP_PATH" ] || [ -z "$DATABRICKS_TOKEN" ]; then
  echo "ERROR: All fields are required" >&2
  exit 1
fi

# Create .env file
ENV_FILE=".env.local"
cat > "$ENV_FILE" << EOF
export DATABRICKS_HOST="$DATABRICKS_HOST"
export DATABRICKS_HTTP_PATH="$DATABRICKS_HTTP_PATH"
export DATABRICKS_TOKEN="$DATABRICKS_TOKEN"
EOF

echo ""
echo "✓ Credentials saved to $ENV_FILE"
echo ""
echo "To activate:"
echo "  source .env.local"
echo ""
echo "IMPORTANT: .env.local is in .gitignore and will NOT be committed to version control."
echo ""
