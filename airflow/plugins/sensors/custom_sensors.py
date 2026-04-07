"""Custom sensors for data arrival and timing triggers."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from airflow.sensors.base import BaseSensorOperator
from airflow.utils.decorators import poke_mode_only

if TYPE_CHECKING:
    from airflow.utils.context import Context


logger = logging.getLogger(__name__)


class S3DataArrivalSensor(BaseSensorOperator):
    """
    Sensor that waits for data files to arrive in S3 or local storage.

    :param data_path: Path to monitor (local or s3://)
    :param file_pattern: Glob pattern for files to match (e.g., '*.parquet')
    :param min_file_size: Minimum file size in bytes (0 = any size)
    """

    template_fields = ["data_path", "file_pattern"]

    def __init__(
        self,
        data_path: str,
        file_pattern: str = "*",
        min_file_size: int = 0,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.data_path = data_path
        self.file_pattern = file_pattern
        self.min_file_size = min_file_size

    @poke_mode_only
    def poke(self, context: Context) -> bool:
        """Check if files matching the pattern exist."""
        logger.info(f"Checking for files at {self.data_path}/{self.file_pattern}")
        
        try:
            if self.data_path.startswith("s3://"):
                return self._check_s3()
            else:
                return self._check_local()
        except Exception as e:
            logger.error(f"Error checking data arrival: {str(e)}")
            return False

    def _check_local(self) -> bool:
        """Check local filesystem for files."""
        path = Path(self.data_path)
        if not path.exists():
            logger.warning(f"Path does not exist: {self.data_path}")
            return False
        
        files = list(path.glob(self.file_pattern))
        
        if not files:
            logger.info(f"No files found matching pattern {self.file_pattern}")
            return False
        
        # Check minimum file size
        for file in files:
            if file.stat().st_size < self.min_file_size:
                logger.info(f"File {file} is smaller than min size {self.min_file_size}")
                return False
        
        logger.info(f"Found {len(files)} files matching pattern {self.file_pattern}")
        return True

    def _check_s3(self) -> bool:
        """Check S3 for files."""
        try:
            import boto3
        except ImportError:
            logger.error("boto3 not installed; cannot check S3")
            return False
        
        # Parse S3 path
        s3_path = self.data_path.replace("s3://", "")
        parts = s3_path.split("/", 1)
        bucket = parts[0]
        prefix = parts[1] if len(parts) > 1 else ""
        
        s3_client = boto3.client("s3")
        
        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
            )
            
            if "Contents" not in response:
                logger.info(f"No objects found at s3://{bucket}/{prefix}")
                return False
            
            logger.info(f"Found {len(response['Contents'])} objects in S3")
            return True
        except Exception as e:
            logger.error(f"S3 check failed: {str(e)}")
            return False


class TimingWindowSensor(BaseSensorOperator):
    """
    Sensor that waits for a specific time window to occur.

    Useful for waiting until a specific hour before triggering downstream tasks.

    :param target_time: Time to trigger (e.g., '06:00' for 6 AM)
    :param timezone: Timezone for comparison (e.g., 'UTC', 'America/New_York')
    """

    def __init__(
        self,
        target_time: str = "06:00",
        timezone: str = "UTC",
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.target_time = target_time
        self.timezone = timezone

    @poke_mode_only
    def poke(self, context: Context) -> bool:
        """Check if current time is at or past target time."""
        try:
            from pytz import timezone as pytz_timezone
        except ImportError:
            logger.error("pytz not installed; cannot check timing window")
            return False
        
        # Parse target time
        target_hour, target_minute = map(int, self.target_time.split(":"))
        
        # Get current time in specified timezone
        tz = pytz_timezone(self.timezone)
        now = datetime.now(tz)
        
        # Check if current time is at or past target time
        target_dt = now.replace(hour=target_hour, minute=target_minute, second=0)
        
        if now >= target_dt:
            logger.info(
                f"Timing window reached: {now.strftime('%H:%M')} >= {self.target_time}"
            )
            return True
        
        wait_seconds = (target_dt - now).total_seconds()
        logger.info(
            f"Waiting until {self.target_time}; {wait_seconds:.0f}s remaining"
        )
        return False
