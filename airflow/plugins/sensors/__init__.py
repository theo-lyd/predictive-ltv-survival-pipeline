"""Custom sensor exports for Airflow plugins."""

try:
	from .custom_sensors import S3DataArrivalSensor, TimingWindowSensor
except ImportError:
	from custom_sensors import S3DataArrivalSensor, TimingWindowSensor

__all__ = ["S3DataArrivalSensor", "TimingWindowSensor"]
