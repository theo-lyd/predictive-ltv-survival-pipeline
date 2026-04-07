"""Custom Airflow operators for pipeline tasks.

Includes operators for:
- Triggering Airbyte syncs
- Running dbt commands
- Executing PySpark jobs
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.plugins_manager import AirflowPlugin

if TYPE_CHECKING:
    from airflow.utils.context import Context

from hooks.airbyte_hook import AirbyteHook


logger = logging.getLogger(__name__)


class AirbyteSyncOperator(BaseOperator):
    """
    Trigger an Airbyte sync and wait for completion.

    :param airbyte_conn_id: Airflow connection ID for Airbyte
    :param airbyte_connection_id: UUID of the Airbyte connection to sync
    :param timeout_seconds: Max seconds to wait for sync completion (0 = no timeout)
    """

    template_fields = ["airbyte_connection_id"]

    def __init__(
        self,
        airbyte_conn_id: str = "airbyte_default",
        airbyte_connection_id: str | None = None,
        timeout_seconds: int = 3600,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.airbyte_conn_id = airbyte_conn_id
        self.airbyte_connection_id = airbyte_connection_id
        self.timeout_seconds = timeout_seconds

    def execute(self, context: Context) -> dict[str, Any]:
        """Execute the Airbyte sync."""
        if not self.airbyte_connection_id:
            raise AirflowException(
                "airbyte_connection_id must be provided to AirbyteSyncOperator"
            )

        hook = AirbyteHook(airbyte_conn_id=self.airbyte_conn_id)
        
        # Trigger sync
        logger.info(f"Triggering Airbyte sync for connection {self.airbyte_connection_id}")
        job_info = hook.trigger_sync(self.airbyte_connection_id)
        job_id = job_info.get("job_id")
        
        if not job_id:
            raise AirflowException(
                f"Failed to get job_id from Airbyte sync response: {job_info}"
            )
        
        # Wait for completion
        logger.info(f"Waiting for job {job_id} to complete")
        final_status = hook.wait_for_sync(job_id)
        
        # Push job info to XCom for downstream tasks
        context["task_instance"].xcom_push(key="airbyte_job_id", value=job_id)
        context["task_instance"].xcom_push(key="airbyte_job_status", value=final_status)
        
        logger.info(f"Airbyte sync completed: {job_id}")
        return final_status


class dbtRunOperator(BaseOperator):
    """
    Execute dbt commands (run, test, compile, etc).

    :param dbt_project_path: Path to dbt project root
    :param dbt_command: dbt command to run (e.g., 'run', 'test', 'run --select tag:daily')
    :param vars_dict: dbt variables to pass (--vars '{"key": "value"}')
    """

    template_fields = ["dbt_command", "vars_dict"]

    def __init__(
        self,
        dbt_project_path: str = ".",
        dbt_command: str = "run",
        vars_dict: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.dbt_project_path = dbt_project_path
        self.dbt_command = dbt_command
        self.vars_dict = vars_dict or {}

    def execute(self, context: Context) -> int:
        """Execute the dbt command."""
        import subprocess
        import json

        # Build dbt command
        cmd = ["dbt", self.dbt_command, "--project-dir", self.dbt_project_path]
        
        # Add variables if provided
        if self.vars_dict:
            cmd.extend(["--vars", json.dumps(self.vars_dict)])
        
        logger.info(f"Executing: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        stdout, stderr = process.communicate()
        
        if stdout:
            logger.info(f"dbt stdout:\n{stdout}")
        if stderr:
            logger.error(f"dbt stderr:\n{stderr}")
        
        if process.returncode != 0:
            raise AirflowException(
                f"dbt command failed with return code {process.returncode}\n{stderr}"
            )
        
        logger.info(f"dbt {self.dbt_command} completed successfully")
        return process.returncode


class PythonIngestOperator(BaseOperator):
    """
    Execute a Python ingestion script (e.g., Bronze data loading).

    :param script_module: Python module path (e.g., 'src.ltv_pipeline.ingestion')
    :param script_function: Function to call (e.g., 'load_bronze_from_csv')
    :param kwargs: Arguments to pass to the function
    """

    template_fields = ["script_kwargs"]

    def __init__(
        self,
        script_module: str,
        script_function: str = "main",
        script_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.script_module = script_module
        self.script_function = script_function
        self.script_kwargs = script_kwargs or {}

    def execute(self, context: Context) -> Any:
        """Execute the Python script/function."""
        import importlib
        
        logger.info(
            f"Executing {self.script_module}.{self.script_function} "
            f"with kwargs: {self.script_kwargs}"
        )
        
        try:
            module = importlib.import_module(self.script_module)
            func = getattr(module, self.script_function)
            result = func(**self.script_kwargs)
            
            logger.info(f"Python script completed successfully")
            return result
        except (ImportError, AttributeError) as e:
            raise AirflowException(
                f"Failed to import {self.script_module}.{self.script_function}: {str(e)}"
            ) from e
        except Exception as e:
            raise AirflowException(
                f"Python script failed: {str(e)}"
            ) from e


# Plugin registration
class PipelineOperatorsPlugin(AirflowPlugin):
    """Register custom operators with Airflow."""

    name = "pipeline_operators"
    operators = [AirbyteSyncOperator, dbtRunOperator, PythonIngestOperator]
    hooks = [AirbyteHook]
