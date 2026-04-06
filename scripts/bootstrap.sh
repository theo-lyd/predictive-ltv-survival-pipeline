#!/usr/bin/env bash
#
# Bootstrap the Predictive LTV Survival Pipeline project
#
# Usage: bash scripts/bootstrap.sh
#
# This script performs one-time setup for a new contributor:
# 1. Validates Python and Java installation
# 2. Creates virtual environment (optional)
# 3. Installs Python dependencies
# 4. Validates dbt profile configuration
# 5. Initializes directory structure

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Predictive LTV Survival Pipeline Bootstrap${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check Python
echo -e "${YELLOW}[1/6] Checking Python installation...${NC}"
if ! command -v python &> /dev/null; then
  echo -e "${RED}ERROR: Python not found${NC}" >&2
  exit 1
fi
PYTHON_VERSION=$(python --version)
echo -e "${GREEN}✓ Found: $PYTHON_VERSION${NC}"

# Check Java
echo ""
echo -e "${YELLOW}[2/6] Checking Java installation...${NC}"
if command -v java &> /dev/null; then
  JAVA_VERSION=$(java -version 2>&1 | head -1)
  echo -e "${GREEN}✓ Found: $JAVA_VERSION${NC}"
else
  echo -e "${YELLOW}! Java not found (required for Spark). Skip if using Databricks SQL.${NC}"
fi

# Install dependencies
echo ""
echo -e "${YELLOW}[3/6] Installing Python dependencies...${NC}"
python -m pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .dbt directory if needed
echo ""
echo -e "${YELLOW}[4/6] Configuring dbt profile...${NC}"
DBT_DIR="${HOME}/.dbt"
if [ ! -d "$DBT_DIR" ]; then
  mkdir -p "$DBT_DIR"
  echo -e "${GREEN}✓ Created $DBT_DIR${NC}"
fi

if [ ! -f "$DBT_DIR/profiles.yml" ]; then
  echo -e "${YELLOW}! dbt profiles.yml not found at $DBT_DIR/profiles.yml${NC}"
  echo -e "${YELLOW}  Please copy profiles.yml.example to $DBT_DIR/profiles.yml and fill in your Databricks credentials${NC}"
  echo ""
  echo -e "${YELLOW}  Steps:${NC}"
  echo -e "${YELLOW}    1. cp profiles.yml.example $DBT_DIR/profiles.yml${NC}"
  echo -e "${YELLOW}    2. Edit $DBT_DIR/profiles.yml with your Databricks host, path, and token${NC}"
  echo -e "${YELLOW}    3. Run: dbt debug${NC}"
else
  echo -e "${GREEN}✓ dbt profiles.yml exists${NC}"
fi

# Create directory structure
echo ""
echo -e "${YELLOW}[5/6] Initializing project directories...${NC}"
mkdir -p data/{bronze,silver,gold} logs
echo -e "${GREEN}✓ Created data directories (Bronze/Silver/Gold)${NC}"

# Final validation
echo ""
echo -e "${YELLOW}[6/6] Validating setup...${NC}"
if python -c "import dbt_databricks, great_expectations" 2>/dev/null; then
  echo -e "${GREEN}✓ Core dependencies verified${NC}"
else
  echo -e "${YELLOW}! Some dependencies may not be installed${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Bootstrap complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "${YELLOW}  1. Configure Databricks credentials:${NC}"
echo -e "${YELLOW}     export DATABRICKS_HOST=<your-host>${NC}"
echo -e "${YELLOW}     export DATABRICKS_TOKEN=<your-token>${NC}"
echo -e "${YELLOW}  2. Test dbt connection:${NC}"
echo -e "${YELLOW}     dbt debug${NC}"
echo -e "${YELLOW}  3. Run project validation:${NC}"
echo -e "${YELLOW}     make validate${NC}"
echo ""
