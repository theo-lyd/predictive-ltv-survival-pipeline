"""Airbyte API Hook for Airflow.

Provides methods to interact with Airbyte instance for triggering syncs,
checking sync status, and retrieving connection information.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import requests
from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook


logger = logging.getLogger(__name__)


class AirbyteHook(BaseHook):
    """
    Integration hook for Airbyte API.

    Supports triggering syncs, checking status, and retrieving metadata.

    :param airbyte_conn_id: Connection ID to use (default: airbyte_default)
    :param api_version: Airbyte API version (default: v1)
    """

    conn_name_attr = "airbyte_conn_id"
    default_conn_name = "airbyte_default"
    conn_type = "airbyte"
    hook_name = "Airbyte"

    def __init__(
        self,
        airbyte_conn_id: str = default_conn_name,
        api_version: str = "v1",
    ):
        self.airbyte_conn_id = airbyte_conn_id
        self.api_version = api_version
        self.base_url: str | None = None
        self.session: requests.Session | None = None

    def get_conn(self) -> requests.Session:
        """Get or create a session connection to Airbyte."""
        if self.session is None:
            conn = BaseHook.get_connection(self.airbyte_conn_id)
            
            # Build base URL from connection host and port
            scheme = conn.schema or "http"
            host = conn.host
            port = conn.port or 8000
            self.base_url = f"{scheme}://{host}:{port}/api/{self.api_version}"
            
            logger.info(f"Connecting to Airbyte at {self.base_url}")
            
            self.session = requests.Session()
            
            # Add authentication if provided
            if conn.login and conn.password:
                self.session.auth = (conn.login, conn.password)
        
        return self.session

    def trigger_sync(self, connection_id: str) -> dict[str, Any]:
        """
        Trigger a sync for the specified Airbyte connection.

        :param connection_id: UUID of the Airbyte connection to sync
        :return: Job info dict containing job_id and status
        """
        session = self.get_conn()
        
        url = f"{self.base_url}/connections/{connection_id}/sync"
        
        try:
            response = session.post(
                url,
                json={},
                timeout=30,
            )
            response.raise_for_status()
            job_info = response.json()
            logger.info(f"Triggered sync for connection {connection_id}: {job_info}")
            return job_info
        except requests.exceptions.RequestException as e:
            raise AirflowException(
                f"Failed to trigger Airbyte sync for connection {connection_id}: {str(e)}"
            ) from e

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """
        Get the status of an Airbyte job.

        :param job_id: UUID of the Airbyte job
        :return: Job status dict
        """
        session = self.get_conn()
        
        url = f"{self.base_url}/jobs/{job_id}"
        
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            job_status = response.json()
            logger.info(f"Job {job_id} status: {job_status.get('status', 'unknown')}")
            return job_status
        except requests.exceptions.RequestException as e:
            raise AirflowException(
                f"Failed to get Airbyte job status for job {job_id}: {str(e)}"
            ) from e

    def wait_for_sync(
        self,
        job_id: str,
        max_attempts: int = 360,  # 60 minutes at 10s intervals
        poll_interval: int = 10,
    ) -> dict[str, Any]:
        """
        Wait for an Airbyte sync job to complete.

        :param job_id: UUID of the sync job
        :param max_attempts: Max number of status checks
        :param poll_interval: Seconds between status checks
        :return: Final job status
        """
        import time
        
        attempt = 0
        
        while attempt < max_attempts:
            job_status = self.get_job_status(job_id)
            status = job_status.get("status")
            
            if status == "succeeded":
                logger.info(f"Job {job_id} succeeded")
                return job_status
            elif status == "failed":
                raise AirflowException(
                    f"Airbyte job {job_id} failed: {job_status.get('failure_reason', 'unknown')}"
                )
            elif status == "cancelled":
                raise AirflowException(f"Airbyte job {job_id} was cancelled")
            
            # Still running, wait and retry
            logger.info(f"Job {job_id} still executing (attempt {attempt + 1}/{max_attempts})")
            time.sleep(poll_interval)
            attempt += 1
        
        raise AirflowException(
            f"Airbyte job {job_id} did not complete after {max_attempts * poll_interval}s"
        )

    def get_connection_info(self, connection_id: str) -> dict[str, Any]:
        """
        Get metadata about an Airbyte connection.

        :param connection_id: UUID of the connection
        :return: Connection info dict
        """
        session = self.get_conn()
        
        url = f"{self.base_url}/connections/{connection_id}"
        
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            conn_info = response.json()
            logger.info(f"Retrieved connection {connection_id} info")
            return conn_info
        except requests.exceptions.RequestException as e:
            raise AirflowException(
                f"Failed to get Airbyte connection info for {connection_id}: {str(e)}"
            ) from e
