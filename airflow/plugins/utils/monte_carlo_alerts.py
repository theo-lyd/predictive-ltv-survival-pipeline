"""
Monte Carlo Alert Handlers and Integration for Phase 4 Batch 4.

Integrates Monte Carlo incidents with Slack notifications and error escalation.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from airflow.exceptions import AirflowException
from airflow.models import Variable


logger = logging.getLogger(__name__)


class MonteCarloAlertHandler:
    """Handles Monte Carlo incidents and routes to appropriate notification channels."""

    def __init__(self, slack_client=None):
        """
        Initialize alert handler.

        Args:
            slack_client: Optional pre-configured Slack client (for testing)
        """
        self.slack_client = slack_client
        self._initialize_channels()

    def _initialize_channels(self):
        """Initialize notification channels from Airflow variables."""
        try:
            self.slack_channel_alerts = Variable.get("MC_SLACK_CHANNEL_ALERTS", "#data-alerts")
            self.slack_channel_critical = Variable.get(
                "MC_SLACK_CHANNEL_CRITICAL", "#data-critical"
            )
            self.email_recipients = Variable.get(
                "MC_EMAIL_RECIPIENTS", "data-engineering@company.com"
            ).split(",")
            self.pagerduty_key = Variable.get("PAGERDUTY_INTEGRATION_KEY", None)
        except Exception as e:
            logger.warning(f"Failed to load notification channels: {e}")
            self.slack_channel_alerts = "#data-alerts"
            self.slack_channel_critical = "#data-critical"
            self.email_recipients = []
            self.pagerduty_key = None

    def route_incident(
        self,
        incident: Dict[str, Any],
        layer: str,
        raise_on_critical: bool = True,
    ) -> None:
        """
        Route incident to appropriate notification channels based on severity and layer.

        Args:
            incident: Incident dictionary from Monte Carlo API
            layer: Pipeline layer (bronze, silver, gold)

        Raises:
            AirflowException: If incident is CRITICAL severity
        """
        severity = incident.get("severity", "MEDIUM").upper()

        logger.info(
            f"Routing {layer} incident {incident.get('id')}: "
            f"severity={severity}, table={incident.get('table')}"
        )

        # Send notification
        self._send_notification(incident, layer, severity)

        # Escalate if needed
        if severity == "CRITICAL":
            self._escalate_incident(incident, layer)
            if raise_on_critical:
                raise AirflowException(
                    f"CRITICAL data quality incident detected in {layer} layer: "
                    f"{incident.get('description')}"
                )

        # Log for audit
        self._log_incident(incident, layer, severity)

    def _send_notification(self, incident: Dict, layer: str, severity: str) -> None:
        """Send incident notification to Slack."""
        try:
            from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator

            message = self._format_incident_message(incident, layer, severity)
            channel = self._select_channel(severity)
            incident_id = str(incident.get("id", "unknown")).replace("-", "_")

            # Try to send via Slack connection if configured.
            try:
                SlackWebhookOperator(
                    task_id=f"notify_incident_{incident_id}",
                    http_conn_id="slack_webhook",
                    message=message,
                    channel=channel,
                ).execute({})
            except Exception as e:
                logger.warning(f"Failed to send Slack notification: {e}")

        except ImportError:
            logger.warning("Slack provider not available")

    def _select_channel(self, severity: str) -> str:
        """Select appropriate Slack channel based on severity."""
        if severity == "CRITICAL":
            return self.slack_channel_critical
        elif severity == "HIGH":
            return self.slack_channel_alerts
        else:
            return self.slack_channel_alerts

    def _format_incident_message(self, incident: Dict, layer: str, severity: str) -> str:
        """Format incident as Slack message."""
        message = f"""
🚨 *Data Quality Alert - {severity}*

*Layer*: {layer.upper()}
*Table*: {incident.get('table', 'Unknown')}
*Incident ID*: {incident.get('id')}
*Type*: {incident.get('type', 'Unknown')}
*Description*: {incident.get('description', 'No description')}
*Created*: {incident.get('createdOn', 'Unknown')}

*Remediation*:
• Check Monte Carlo Console for details
• Review affected table schemas and volumes
• Investigate upstream data source
• Resolve when root cause is identified
        """.strip()

        return message

    def _escalate_incident(self, incident: Dict, layer: str) -> None:
        """Escalate CRITICAL incident to PagerDuty/on-call engineer."""
        try:
            if not self.pagerduty_key:
                logger.warning("PagerDuty integration key not configured")
                return

            import requests

            pagerduty_payload = {
                "routing_key": self.pagerduty_key,
                "event_action": "trigger",
                "dedup_key": f"mc-incident-{incident.get('id')}",
                "payload": {
                    "summary": f"CRITICAL: {incident.get('description')} in {layer}",
                    "severity": "critical",
                    "source": "Monte Carlo Data",
                    "custom_details": {
                        "incident_id": incident.get("id"),
                        "table": incident.get("table"),
                        "layer": layer,
                        "created": incident.get("createdOn"),
                    },
                },
            }

            response = requests.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=pagerduty_payload,
                timeout=10,
            )
            response.raise_for_status()
            logger.info(f"Incident escalated to PagerDuty: {incident.get('id')}")

        except Exception as e:
            logger.error(f"Failed to escalate to PagerDuty: {e}")

    def _log_incident(self, incident: Dict, layer: str, severity: str) -> None:
        """Log incident for audit trail."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "incident_id": incident.get("id"),
            "layer": layer,
            "severity": severity,
            "table": incident.get("table"),
            "description": incident.get("description"),
        }
        logger.info(f"Incident logged: {json.dumps(log_entry)}")

    def check_layer_health(self, hook, layer: str, fail_on_critical: bool = True) -> Dict:
        """
        Check Monte Carlo health for all tables in a given layer.

        Args:
            hook: MonteCarloHook instance
            layer: Pipeline layer (bronze, silver, gold)
            fail_on_critical: If True, raise exception on CRITICAL incidents

        Returns:
            Dictionary with layer health status and incidents

        Raises:
            AirflowException: If critical incidents found and fail_on_critical=True
        """
        from config.phase_4_batch_4_monte_carlo_config import VOLUME_MONITORS

        layer_tables = {
            name: config["table_name"]
            for name, config in VOLUME_MONITORS.items()
            if name.startswith(layer)
        }

        health_status = {
            "layer": layer,
            "timestamp": datetime.utcnow().isoformat(),
            "tables": {},
            "critical_incidents": [],
            "overall_status": "healthy",
        }

        critical_found = False

        for table_short_name, table_full_name in layer_tables.items():
            try:
                health = hook.get_asset_health(table_full_name, include_incidents=True)
                status = health.get("health", {}).get("overallStatus", "UNKNOWN")
                incidents = health.get("incidents", [])

                table_health = {
                    "table": table_full_name,
                    "status": status,
                    "incident_count": len(incidents),
                    "incidents": [],
                }

                for incident in incidents:
                    incident_severity = incident.get("severity", "MEDIUM")
                    table_health["incidents"].append(
                        {
                            "id": incident.get("id"),
                            "type": incident.get("type"),
                            "severity": incident_severity,
                        }
                    )

                    if incident_severity == "CRITICAL":
                        critical_found = True
                        health_status["critical_incidents"].append(
                            {
                                "table": table_full_name,
                                "incident": incident,
                            }
                        )

                    # Route each incident without raising inside the per-table processing loop.
                    self.route_incident(incident, layer, raise_on_critical=False)

                health_status["tables"][table_short_name] = table_health

            except Exception as e:
                logger.error(f"Failed to check health for {table_full_name}: {e}")
                health_status["tables"][table_short_name] = {
                    "table": table_full_name,
                    "status": "ERROR",
                    "error": str(e),
                }
                health_status["overall_status"] = "check_failed"

        # Determine overall status
        if critical_found:
            health_status["overall_status"] = "critical"
        elif any(t.get("status") == "BAD" for t in health_status["tables"].values()):
            health_status["overall_status"] = "degraded"
        elif health_status["overall_status"] != "check_failed":
            health_status["overall_status"] = "healthy"

        logger.info(f"Layer {layer} health check complete: {health_status['overall_status']}")

        if fail_on_critical and critical_found:
            raise AirflowException(
                f"CRITICAL incidents found in {layer} layer. "
                f"Count: {len(health_status['critical_incidents'])}"
            )

        return health_status

    def get_layer_incidents(
        self,
        hook,
        layer: str,
        status: str = "OPEN",
        include_resolved_after: Optional[timedelta] = None,
    ) -> List[Dict]:
        """
        Get all incidents for tables in a layer.

        Args:
            hook: MonteCarloHook instance
            layer: Pipeline layer (bronze, silver, gold)
            status: Filter by status (OPEN, RESOLVED, MUTED)
            include_resolved_after: Include resolved incidents from last N minutes

        Returns:
            List of incident dictionaries
        """
        from config.phase_4_batch_4_monte_carlo_config import VOLUME_MONITORS

        layer_tables = [
            config["table_name"]
            for name, config in VOLUME_MONITORS.items()
            if name.startswith(layer)
        ]

        all_incidents = []
        for table_name in layer_tables:
            try:
                incidents = hook.list_incidents(status=status, asset_name=table_name, limit=100)
                all_incidents.extend(incidents)
            except Exception as e:
                logger.warning(f"Failed to fetch incidents for {table_name}: {e}")

        return all_incidents


class IncidentResponseHandler:
    """Handles incident response and remediation workflows."""

    @staticmethod
    def resolve_volume_incident(hook, incident_id: str, remediation_note: str) -> Dict[str, Any]:
        """
        Resolve a volume anomaly incident.

        Args:
            hook: MonteCarloHook instance
            incident_id: Unique incident identifier
            remediation_note: Description of remediation action taken

        Returns:
            Resolution status
        """
        resolution = hook.resolve_incident(
            incident_id=incident_id,
            resolution_note=f"Resolved by automated pipeline: {remediation_note}",
        )
        logger.info(f"Resolved incident {incident_id}: {resolution}")
        return resolution

    @staticmethod
    def get_incident_context(hook, incident_id: str) -> Dict[str, Any]:
        """
        Get full context for an incident (metrics, historical trends, etc.).

        Args:
            hook: MonteCarloHook instance
            incident_id: Unique incident identifier

        Returns:
            Incident context with metrics
        """
        # This would require additional Monte Carlo API methods
        # For now, return basic structure
        return {
            "incident_id": incident_id,
            "retrieved_at": datetime.utcnow().isoformat(),
            "context_available": False,  # Requires MC API enhancement
        }


def create_mc_health_check_task(layer: str, fail_on_critical: bool = True):
    """
    Create a health check task for a given layer.

    This factory function creates a task that checks Monte Carlo health
    for all tables in a layer and optionally fails if critical incidents exist.

    Args:
        layer: Pipeline layer (bronze, silver, gold)
        fail_on_critical: If True, task fails on critical incidents

    Returns:
        Python callable for use with PythonOperator
    """

    def health_check_task(**context):
        from hooks.monte_carlo_hook import MonteCarloHook

        hook = MonteCarloHook()
        handler = MonteCarloAlertHandler()

        health = handler.check_layer_health(
            hook,
            layer=layer,
            fail_on_critical=fail_on_critical,
        )

        context["task_instance"].xcom_push(
            key=f"mc_health_{layer}",
            value=health,
        )

        return health

    return health_check_task
