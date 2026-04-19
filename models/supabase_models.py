"""
Type definitions for Supabase database models.
These TypedDict definitions map to tables in the Supabase schema.
"""

from typing import TypedDict, Optional
from datetime import datetime


class SensorReading(TypedDict, total=False):
    """Represents a sensor_data row in Supabase"""
    log_id: int
    sensor_id: int
    value: float
    logged_at: datetime


class ControlLog(TypedDict, total=False):
    """Represents a control_logs row in Supabase"""
    log_id: int
    device_id: int
    user_id: int
    action: str  # e.g., "ON", "OFF"
    logged_at: datetime


class AlertEvent(TypedDict, total=False):
    """Represents an alerts row in Supabase"""
    alert_id: int
    threshold_id: int
    start_time: datetime
    end_time: Optional[datetime]
    is_resolved: bool


class SensorInfo(TypedDict, total=False):
    """Represents a sensors row in Supabase"""
    sensor_id: int
    sensor_type: str  # e.g., "TEMPERATURE", "HUMIDITY"
    unit: str  # e.g., "°C", "%"


class DeviceInfo(TypedDict, total=False):
    """Represents a devices row in Supabase"""
    device_id: int
    name: str
    device_type: str  # e.g., "PUMP", "LIGHT"
    status: bool
    is_automatic: bool


class UserInfo(TypedDict, total=False):
    """Represents a users row in Supabase"""
    user_id: int
    username: str
    email: Optional[str]
    password: str
