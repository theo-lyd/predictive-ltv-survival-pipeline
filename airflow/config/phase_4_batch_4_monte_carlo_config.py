"""
Monte Carlo Data Monitoring Configuration for Phase 4 Batch 4.

Defines monitors for Bronze, Silver, and Gold layers with thresholds and SLAs.
"""

from datetime import timedelta

# ============================================================================
# Volume Monitor Configurations
# ============================================================================

VOLUME_MONITORS = {
    # Bronze Layer: Ingested raw data
    "bronze_customers": {
        "table_name": "data.bronze.customers",
        "monitor_name": "Bronze: Customer Row Count",
        "lower_threshold": 100,       # At least 100 rows expected
        "upper_threshold": 10_000_000, # Max 10M (sanity check)
        "description": "Volume monitor for ingested customer records",
        "severity": "high",
    },
    
    "bronze_billing": {
        "table_name": "data.bronze.billing",
        "monitor_name": "Bronze: Billing Row Count",
        "lower_threshold": 50,
        "upper_threshold": 50_000_000,
        "description": "Volume monitor for ingested billing records",
        "severity": "high",
    },
    
    # Silver Layer: Staged/deduplicated data
    "silver_customers": {
        "table_name": "data.silver.customers",
        "monitor_name": "Silver: Customer Dimension",
        "lower_threshold": 80,  # Some loss ok (duplicates removed)
        "upper_threshold": 10_000_000,
        "description": "Volume monitor for deduplicated customers",
        "severity": "medium",
    },
    
    "silver_billing": {
        "table_name": "data.silver.billing",
        "monitor_name": "Silver: Billing Facts",
        "lower_threshold": 40,
        "upper_threshold": 50_000_000,
        "description": "Volume monitor for normalized billing records",
        "severity": "medium",
    },
    
    # Gold Layer: Features and metrics
    "gold_ltv": {
        "table_name": "data.gold.fct_customer_ltv",
        "monitor_name": "Gold: Customer LTV Fact Table",
        "lower_threshold": 50,  # Fewer unique customers than billing transactions
        "upper_threshold": 1_000_000,
        "description": "Volume monitor for LTV fact table",
        "severity": "high",
    },
    
    "gold_survival": {
        "table_name": "data.gold.fct_survival_cohort_summary",
        "monitor_name": "Gold: Survival Cohort Summary",
        "lower_threshold": 10,  # Cohort summaries
        "upper_threshold": 100_000,
        "description": "Volume monitor for survival curve data",
        "severity": "medium",
    },
}

# ============================================================================
# Freshness Monitor Configurations
# ============================================================================

FRESHNESS_MONITORS = {
    # Bronze Layer: Should be fresh daily
    "bronze_customers_freshness": {
        "table_name": "data.bronze.customers",
        "monitor_name": "Bronze: Customer Data Freshness",
        "sla_minutes": 60,  # Data should arrive within 1 hour of daily run
        "description": "Freshness monitor for customer ingestion",
        "severity": "high",
    },
    
    "bronze_billing_freshness": {
        "table_name": "data.bronze.billing",
        "monitor_name": "Bronze: Billing Data Freshness",
        "sla_minutes": 90,  # Billing may take longer
        "description": "Freshness monitor for billing ingestion",
        "severity": "high",
    },
    
    # Silver Layer: Should complete within 2 hours of Bronze arrival
    "silver_customers_freshness": {
        "table_name": "data.silver.customers",
        "monitor_name": "Silver: Customer Staging Freshness",
        "sla_minutes": 120,  # 2 hours after Bronze
        "description": "Freshness monitor for Silver staging",
        "severity": "medium",
    },
    
    # Gold Layer: Should complete within 3 hours of Bronze
    "gold_ltv_freshness": {
        "table_name": "data.gold.fct_customer_ltv",
        "monitor_name": "Gold: LTV Metrics Freshness",
        "sla_minutes": 180,  # 3 hours after Bronze
        "description": "Freshness monitor for Gold metrics",
        "severity": "high",
    },
}

# ============================================================================
# Schema Change Monitors
# ============================================================================

SCHEMA_MONITORS = {
    # Bronze: Should never change (raw ingestion)
    "bronze_customers_schema": {
        "table_name": "data.bronze.customers",
        "monitor_name": "Bronze: Customer Schema - Detect Changes",
        "description": "Alerts on unexpected schema changes (columns added/removed/type changed)",
        "severity": "high",
    },
    
    "bronze_billing_schema": {
        "table_name": "data.bronze.billing",
        "monitor_name": "Bronze: Billing Schema - Detect Changes",
        "description": "Alerts on unexpected billing schema changes",
        "severity": "high",
    },
    
    # Silver: Schema changes indicate transformation bugs
    "silver_customers_schema": {
        "table_name": "data.silver.customers",
        "monitor_name": "Silver: Customer Schema - Detect Changes",
        "description": "Alerts on Silver schema drift",
        "severity": "medium",
    },
    
    # Gold: Schema changes break downstream (BI tools, APIs)
    "gold_ltv_schema": {
        "table_name": "data.gold.fct_customer_ltv",
        "monitor_name": "Gold: LTV Schema - Detect Changes",
        "description": "Alerts on LTV fact table schema changes",
        "severity": "high",
    },
}

# ============================================================================
# Alert Thresholds and Severity Levels
# ============================================================================

ALERT_THRESHOLDS = {
    # Volume threshold alerts
    "volume": {
        "high_severity": {
            "threshold_percent": 20,  # Alert if >20% below expected
            "requires_ack": True,
            "escalate_after_minutes": 30,
        },
        "medium_severity": {
            "threshold_percent": 30,  # Alert if >30% below expected
            "requires_ack": True,
            "escalate_after_minutes": 60,
        },
        "low_severity": {
            "threshold_percent": 50,  # Alert if >50% below expected
            "requires_ack": False,
            "escalate_after_minutes": 120,
        },
    },
    
    # Freshness threshold alerts
    "freshness": {
        "high_severity": {
            "latency_minutes": 30,    # Alert if 30 min late
            "requires_ack": True,
            "escalate_after_minutes": 15,
        },
        "medium_severity": {
            "latency_minutes": 120,   # Alert if 2 hours late
            "requires_ack": True,
            "escalate_after_minutes": 60,
        },
        "low_severity": {
            "latency_minutes": 240,   # Alert if 4 hours late
            "requires_ack": False,
            "escalate_after_minutes": 120,
        },
    },
    
    # Schema change alerts (always high severity)
    "schema": {
        "high_severity": {
            "threshold_columns_changed": 1,  # Alert if ANY column changes
            "requires_ack": True,
            "escalate_after_minutes": 10,
        },
    },
}

# ============================================================================
# Incident Routing and Escalation Rules
# ============================================================================

INCIDENT_ROUTING = {
    # Bronze layer issues
    "bronze": {
        "severity_levels": ["high", "medium", "low"],
        "primary_channel": "slack",
        "slack_channel": "#data-alerts",
        "email_recipients": ["data-engineering@company.com"],
        "pagerduty_service_id": "bronze_ingestion_service",
        "escalate_to_pagerduty": True,  # Bronze failures are critical
        "escalation_rules": [
            {
                "severity": "high",
                "after_minutes_unresolved": 15,
                "action": "page_on_call_engineer",
            },
            {
                "severity": "medium",
                "after_minutes_unresolved": 60,
                "action": "email_team_lead",
            },
        ],
    },
    
    # Silver layer issues
    "silver": {
        "severity_levels": ["high", "medium", "low"],
        "primary_channel": "slack",
        "slack_channel": "#data-alerts",
        "email_recipients": ["data-engineering@company.com"],
        "pagerduty_service_id": None,  # Silver failures can wait
        "escalate_to_pagerduty": False,
        "escalation_rules": [
            {
                "severity": "high",
                "after_minutes_unresolved": 60,
                "action": "email_team_lead",
            },
            {
                "severity": "medium",
                "after_minutes_unresolved": 120,
                "action": "create_jira_ticket",
            },
        ],
    },
    
    # Gold layer issues
    "gold": {
        "severity_levels": ["high", "medium", "low"],
        "primary_channel": "slack",
        "slack_channel": "#data-alerts",
        "email_recipients": ["analytics-team@company.com", "data-engineering@company.com"],
        "pagerduty_service_id": "gold_metrics_service",
        "escalate_to_pagerduty": True,  # Gold metrics drive business decisions
        "escalation_rules": [
            {
                "severity": "high",
                "after_minutes_unresolved": 30,
                "action": "page_on_call_engineer",
            },
            {
                "severity": "medium",
                "after_minutes_unresolved": 120,
                "action": "email_analytics_team",
            },
        ],
    },
}

# ============================================================================
# Monitor Baseline Settings
# ============================================================================

MONITOR_BASELINES = {
    # Learning period: First 14 days of monitor data
    "learning_period_days": 14,
    
    # Minimum data points to establish baseline
    "min_baseline_points": 10,
    
    # Sensitivity: how much deviation triggers alert
    "anomaly_sensitivity": "medium",  # low, medium, high
    
    # Time window for anomaly detection (rolling window)
    "detection_window_days": 7,
}

# ============================================================================
# Example Usage
# ============================================================================

"""
from airflow.plugins.hooks.monte_carlo_hook import MonteCarloHook
from airflow.config.phase_4_batch_4_monte_carlo_config import (
    VOLUME_MONITORS, FRESHNESS_MONITORS, SCHEMA_MONITORS
)

hook = MonteCarloHook()

# Create volume monitor
for monitor_config in VOLUME_MONITORS.values():
    hook.create_volume_monitor(
        name=monitor_config["monitor_name"],
        asset_name=monitor_config["table_name"],
        lower_threshold=monitor_config["lower_threshold"],
        upper_threshold=monitor_config["upper_threshold"],
    )

# Create freshness monitor
for monitor_config in FRESHNESS_MONITORS.values():
    hook.create_freshness_monitor(
        name=monitor_config["monitor_name"],
        asset_name=monitor_config["table_name"],
        freshness_sla_minutes=monitor_config["sla_minutes"],
    )

# Create schema monitor
for monitor_config in SCHEMA_MONITORS.values():
    hook.create_schema_monitor(
        name=monitor_config["monitor_name"],
        asset_name=monitor_config["table_name"],
    )

# Check asset health
health = hook.get_asset_health("data.gold.fct_customer_ltv")
print(f"LTV table health: {health['health']['overallStatus']}")

# List open incidents
incidents = hook.list_incidents(status="OPEN")
for incident in incidents:
    print(f"Open incident: {incident['id']} - {incident['severity']}")
"""
