#!/bin/bash
# Development Airflow startup script
# Starts both scheduler and webserver for local development
#
# Usage:
#   bash airflow/start_airflow_dev.sh
#
# Cleanup:
#   pkill -f "airflow scheduler"
#   pkill -f "airflow webserver"

set -e

export AIRFLOW_HOME=/workspaces/predictive-ltv-survival-pipeline/airflow

echo "=========================================="
echo "Airflow Development Mode Startup"
echo "=========================================="
echo "AIRFLOW_HOME: $AIRFLOW_HOME"
echo ""

# Check if database exists
if [ ! -f "$AIRFLOW_HOME/airflow.db" ]; then
    echo "⚠ Airflow database not found. Running initialization..."
    bash "$(dirname "$0")/init_airflow.sh"
    echo ""
fi

echo "Starting Airflow Scheduler in background..."
airflow scheduler --daemon
echo "✓ Scheduler started (PID: $!)"
echo ""

echo "Starting Airflow Webserver..."
echo "✓ Webserver running on http://localhost:8080"
echo ""
echo "To stop:"
echo "  pkill -f 'airflow scheduler'"
echo "  pkill -f 'airflow webserver'"
echo ""

airflow webserver --port 8080
