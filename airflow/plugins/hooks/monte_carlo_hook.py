"""
Monte Carlo Data API Hook for Airflow.

Provides integration with Monte Carlo Data's API for:
- Data quality monitoring (volume, freshness, schema)
- Alert configuration and management
- Incident tracking and escalation
"""

from __future__ import annotations

import json
import logging
from typing import Any
from datetime import datetime, timedelta

import requests
from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook
from airflow.models import Variable


logger = logging.getLogger(__name__)


class MonteCarloHook(BaseHook):
    """
    Integration hook for Monte Carlo Data API.

    Supports creating monitors, querying health metrics, and managing incidents.

    :param monte_carlo_conn_id: Connection ID for Monte Carlo (default: monte_carlo_default)
    :param api_version: Monte Carlo API version (default: v1)
    """

    conn_name_attr = "monte_carlo_conn_id"
    default_conn_name = "monte_carlo_default"
    conn_type = "monte_carlo"
    hook_name = "Monte Carlo"

    def __init__(
        self,
        monte_carlo_conn_id: str = default_conn_name,
        api_version: str = "v1",
    ):
        self.monte_carlo_conn_id = monte_carlo_conn_id
        self.api_version = api_version
        self.base_url: str | None = None
        self.session: requests.Session | None = None
        self.api_key: str | None = None
        self.api_secret: str | None = None

    def get_conn(self) -> requests.Session:
        """Establish connection to Monte Carlo Data."""
        if self.session is None:
            conn = BaseHook.get_connection(self.monte_carlo_conn_id)
            
            # Monte Carlo uses API key and secret from connection
            self.api_key = conn.login or Variable.get("monte_carlo_api_key", "")
            self.api_secret = conn.password or Variable.get("monte_carlo_api_secret", "")
            
            # Base URL
            self.base_url = conn.host or "https://api.montecarlodata.com"
            
            logger.info(f"Connecting to Monte Carlo at {self.base_url}")
            
            self.session = requests.Session()
            
            # Add API key to headers
            if self.api_key:
                self.session.headers.update({
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                })
        
        return self.session

    def graphql_query(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Execute GraphQL query against Monte Carlo API.

        :param query: GraphQL query string
        :param variables: Query variables dict
        :return: Response data dict
        """
        session = self.get_conn()
        
        payload = {
            "query": query,
        }
        if variables:
            payload["variables"] = variables
        
        try:
            response = session.post(
                f"{self.base_url}/api/v1/graphql",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Check for GraphQL errors
            if "errors" in result:
                error_msg = "\n".join([e.get("message", str(e)) for e in result["errors"]])
                raise AirflowException(f"GraphQL error: {error_msg}")
            
            logger.info(f"GraphQL query executed successfully")
            return result.get("data", {})
        except requests.exceptions.RequestException as e:
            raise AirflowException(f"Monte Carlo API request failed: {str(e)}") from e

    def get_asset_health(self, asset_name: str, include_incidents: bool = True) -> dict[str, Any]:
        """
        Get health status of a data asset.

        :param asset_name: Fully qualified asset name (e.g., 'database.schema.table')
        :param include_incidents: Include open incidents
        :return: Health status dict
        """
        query = """
        query GetAssetHealth($fqn: String!, $includeIncidents: Boolean!) {
            asset(fqn: $fqn) {
                fqn
                name
                assetType
                health {
                    overallStatus
                    lastUpdated
                    monitors {
                        id
                        name
                        status
                        lastUpdated
                    }
                }
                incidents @include(if: $includeIncidents) {
                    id
                    status
                    severity
                    createdAt
                    monitors {
                        name
                    }
                }
            }
        }
        """
        
        variables = {
            "fqn": asset_name,
            "includeIncidents": include_incidents,
        }
        
        result = self.graphql_query(query, variables)
        return result.get("asset", {})

    def create_volume_monitor(
        self,
        name: str,
        asset_name: str,
        lower_threshold: int | None = None,
        upper_threshold: int | None = None,
    ) -> dict[str, Any]:
        """
        Create a volume (row count) monitor.

        :param name: Monitor name
        :param asset_name: Fully qualified asset name
        :param lower_threshold: Minimum expected row count
        :param upper_threshold: Maximum expected row count
        :return: Monitor details
        """
        mutation = """
        mutation CreateVolumeMonitor(
            $name: String!
            $fqn: String!
            $lowerThreshold: Long
            $upperThreshold: Long
        ) {
            createVolumeMonitor(input: {
                name: $name
                fqn: $fqn
                lowerThreshold: $lowerThreshold
                upperThreshold: $upperThreshold
            }) {
                monitor {
                    id
                    name
                    status
                }
            }
        }
        """
        
        variables = {
            "name": name,
            "fqn": asset_name,
        }
        
        if lower_threshold is not None:
            variables["lowerThreshold"] = lower_threshold
        if upper_threshold is not None:
            variables["upperThreshold"] = upper_threshold
        
        result = self.graphql_query(mutation, variables)
        return result.get("createVolumeMonitor", {}).get("monitor", {})

    def create_freshness_monitor(
        self,
        name: str,
        asset_name: str,
        freshness_sla_minutes: int,
    ) -> dict[str, Any]:
        """
        Create a freshness (staleness) monitor.

        :param name: Monitor name
        :param asset_name: Fully qualified asset name
        :param freshness_sla_minutes: SLA in minutes (alert if data older than this)
        :return: Monitor details
        """
        mutation = """
        mutation CreateFreshnessMonitor(
            $name: String!
            $fqn: String!
            $freshnessSlaMinutes: Int!
        ) {
            createFreshnessMonitor(input: {
                name: $name
                fqn: $fqn
                freshnessThresholdMinutes: $freshnessSlaMinutes
            }) {
                monitor {
                    id
                    name
                    status
                }
            }
        }
        """
        
        variables = {
            "name": name,
            "fqn": asset_name,
            "freshnessSlaMinutes": freshness_sla_minutes,
        }
        
        result = self.graphql_query(mutation, variables)
        return result.get("createFreshnessMonitor", {}).get("monitor", {})

    def create_schema_monitor(
        self,
        name: str,
        asset_name: str,
    ) -> dict[str, Any]:
        """
        Create a schema change monitor (detects columns added/removed/type changes).

        :param name: Monitor name
        :param asset_name: Fully qualified asset name
        :return: Monitor details
        """
        mutation = """
        mutation CreateSchemaMonitor(
            $name: String!
            $fqn: String!
        ) {
            createSchemaMonitor(input: {
                name: $name
                fqn: $fqn
            }) {
                monitor {
                    id
                    name
                    status
                }
            }
        }
        """
        
        variables = {
            "name": name,
            "fqn": asset_name,
        }
        
        result = self.graphql_query(mutation, variables)
        return result.get("createSchemaMonitor", {}).get("monitor", {})

    def list_incidents(
        self,
        status: str | None = None,
        asset_name: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        List incidents (filtered by status and/or asset).

        :param status: Filter by status (e.g., 'OPEN', 'RESOLVED')
        :param asset_name: Filter by asset FQN
        :param limit: Max incidents to return
        :return: List of incident dicts
        """
        query = """
        query ListIncidents($filter: IncidentFilter!, $limit: Int!) {
            incidents(filter: $filter, limit: $limit) {
                id
                status
                severity
                createdAt
                resolvedAt
                monitors {
                    id
                    name
                }
                asset {
                    fqn
                    name
                }
            }
        }
        """
        
        incident_filter = {}
        if status:
            incident_filter["status"] = status
        if asset_name:
            incident_filter["assetFqn"] = asset_name
        
        variables = {
            "filter": incident_filter,
            "limit": limit,
        }
        
        result = self.graphql_query(query, variables)
        return result.get("incidents", [])

    def resolve_incident(self, incident_id: str, resolution_note: str | None = None) -> dict[str, Any]:
        """
        Mark an incident as resolved.

        :param incident_id: Monte Carlo incident ID
        :param resolution_note: Optional resolution note
        :return: Updated incident dict
        """
        mutation = """
        mutation ResolveIncident($id: String!, $note: String) {
            resolveIncident(input: {id: $id, resolutionNote: $note}) {
                incident {
                    id
                    status
                    resolvedAt
                }
            }
        }
        """
        
        variables = {
            "id": incident_id,
        }
        if resolution_note:
            variables["note"] = resolution_note
        
        result = self.graphql_query(mutation, variables)
        return result.get("resolveIncident", {}).get("incident", {})

    def get_monitor_metrics(
        self,
        monitor_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get metric history for a monitor.

        :param monitor_id: Monte Carlo monitor ID
        :param start_time: Start of time range (default: 7 days ago)
        :param end_time: End of time range (default: now)
        :return: List of metric points
        """
        end_time = end_time or datetime.utcnow()
        start_time = start_time or (end_time - timedelta(days=7))
        
        query = """
        query GetMonitorMetrics($monitorId: String!, $startTime: DateTime!, $endTime: DateTime!) {
            monitor(id: $monitorId) {
                metrics(startTime: $startTime, endTime: $endTime) {
                    timestamp
                    value
                    status
                }
            }
        }
        """
        
        variables = {
            "monitorId": monitor_id,
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
        }
        
        result = self.graphql_query(query, variables)
        monitor = result.get("monitor", {})
        return monitor.get("metrics", [])
