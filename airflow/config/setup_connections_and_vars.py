"""
Airflow Variables and Connections Setup for Phase 4 Batch 2.

This module provides helper functions to set up Airflow Variables and Connections
programmatically. Run this from the Airflow Python shell or as part of initialization.

Usage (from airflow shell):
    exec(open('airflow/config/setup_connections_and_vars.py').read())
    setup_variables()
    setup_connections()
"""

from airflow.models import Connection, Variable
from airflow.utils.db import merge_conn


def setup_variables():
    """Create Airflow Variables needed by the pipeline."""
    
    variables = {
        # Project paths
        "project_root": ".",
        "bronze_data_path": "./data/bronze/customers.csv",
        
        # Airbyte configuration
        "airbyte_conn_id": "airbyte_default",
        "airbyte_connection_id": "{{ airbyte_connection_uuid }}",  # Replace with real UUID
        "airbyte_timeout_seconds": "3600",
        
        # dbt configuration
        "dbt_project_path": ".",
        "dbt_profiles_dir": ".",
        "observation_date": "{{ ds }}",
        
        # Slack notifications (optional)
        "slack_webhook": "",  # Set to Slack webhook URL to enable notifications
        "slack_channel": "#data-alerts",
        
        # Monitoring thresholds
        "alert_on_task_failure": "true",
        "alert_retry_count": "1",
    }
    
    for key, value in variables.items():
        Variable.set(key, value)
        print(f"✓ Set variable: {key}")
    
    print(f"\n✅ Created {len(variables)} Airflow Variables")


def setup_connections():
    """Create Airflow Connections needed by the pipeline."""
    
    # Airbyte connection (HTTP)
    airbyte_conn = Connection(
        conn_id="airbyte_default",
        conn_type="http",
        host="localhost",
        port=8000,
        schema="http",
        description="Connection to local Airbyte instance for API calls",
    )
    
    # Databricks connection (optional, for future PySpark operator)
    databricks_conn = Connection(
        conn_id="databricks_default",
        conn_type="databricks",
        host="<databricks-instance-url>",
        login="<token-id>",
        password="<token-secret>",
        description="Connection to Databricks workspace",
    )
    
    connections = [airbyte_conn, databricks_conn]
    
    for conn in connections:
        merge_conn(conn)
        print(f"✓ Created connection: {conn.conn_id} ({conn.conn_type})")
    
    print(f"\n✅ Created {len(connections)} Airflow Connections")


def setup_all():
    """Set up all variables and connections."""
    print("Setting up Airflow Variables and Connections...\n")
    setup_variables()
    setup_connections()
    print("\n🎉 Airflow configuration complete!")


if __name__ == "__main__":
    setup_all()
