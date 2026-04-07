#!/bin/bash
# Airflow initialization script
# Initializes Airflow database and user account
# 
# Usage:
#   bash airflow/init_airflow.sh
#
# Prerequisites:
#   - AIRFLOW_HOME environment variable must be set
#   - Python venv with Airflow installed
#   - `.venv/bin/activate` sourced

set -e

# Validate AIRFLOW_HOME
if [ -z "$AIRFLOW_HOME" ]; then
    export AIRFLOW_HOME=/workspaces/predictive-ltv-survival-pipeline/airflow
    echo "✓ AIRFLOW_HOME not set, using default: $AIRFLOW_HOME"
fi

echo "=========================================="
echo "Airflow Initialization"
echo "=========================================="
echo "AIRFLOW_HOME: $AIRFLOW_HOME"
echo "AIRFLOW_DAGS_FOLDER: $AIRFLOW_HOME/dags"
echo ""

# Step 1: Initialize Airflow database
echo "[1/4] Initializing Airflow database..."
airflow db init
echo "✓ Database initialized"
echo ""

# Step 2: Create default admin user (if not exists)
echo "[2/4] Creating admin user..."
# Check if user already exists
if airflow users list | grep -q "admin"; then
    echo "✓ Admin user already exists"
else
    airflow users create \
        --username admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@predictive-ltv-pipeline.local \
        --password admin
    echo "✓ Admin user created (username: admin, password: admin)"
fi
echo ""

# Step 3: Verify DAGs folder exists
echo "[3/4] Verifying DAGs folder..."
if [ ! -d "$AIRFLOW_HOME/dags" ]; then
    mkdir -p "$AIRFLOW_HOME/dags"
    echo "✓ Created DAGs folder: $AIRFLOW_HOME/dags"
else
    echo "✓ DAGs folder exists: $AIRFLOW_HOME/dags"
fi
echo ""

# Step 4: List environment
echo "[4/4] Environment verification..."
airflow info | head -20
echo ""

echo "=========================================="
echo "✅ Airflow initialization complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start scheduler (background): airflow scheduler &"
echo "2. Start webserver: airflow webserver"
echo "3. Access Airflow UI: http://localhost:8080"
echo "4. Login with: username=admin, password=admin"
