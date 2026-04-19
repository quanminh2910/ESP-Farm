"""
Repository layer for sensor data and control log operations.
Provides domain-specific methods for persisting farm data to Supabase.
"""

from typing import Optional, List
from datetime import datetime
from config.settings import Settings
from models.supabase_models import SensorReading, ControlLog, AlertEvent
from services.supabase_service import SupabaseClientSingleton
from utils.logger import get_logger

logger = get_logger(__name__)


class SensorDataRepository:
    """Repository for sensor data and control log persistence"""
    
    def __init__(self):
        """Initialize repository with Supabase client singleton"""
        self._supabase = SupabaseClientSingleton()
    
    def save_sensor_reading(
        self,
        sensor_id: int,
        value: float,
        logged_at: Optional[datetime] = None
    ) -> SensorReading:
        """
        Save a sensor reading to the database
        
        Args:
            sensor_id: ID of the sensor (from sensors table)
            value: Sensor reading value
            logged_at: Timestamp of the reading (defaults to now)
        
        Returns:
            SensorReading object with the saved data
        """
        if logged_at is None:
            logged_at = datetime.utcnow()
        
        try:
            data: SensorReading = {
                "sensor_id": sensor_id,
                "value": value,
                "logged_at": logged_at.isoformat(),
            }
            
            result = self._supabase.insert("sensor_data", data)
            logger.info(
                f"[REPO] Saved sensor reading: sensor_id={sensor_id}, "
                f"value={value}, timestamp={logged_at}"
            )
            return result
        except Exception as e:
            logger.error(f"[REPO] Failed to save sensor reading: {str(e)}")
            raise
    
    def save_control_log(
        self,
        device_id: int,
        user_id: int,
        action: str,
        logged_at: Optional[datetime] = None
    ) -> ControlLog:
        """
        Save a control action log to the database
        
        Args:
            device_id: ID of the device being controlled (e.g., pump)
            user_id: ID of the user performing the action (or SYSTEM_USER_ID for automation)
            action: Action performed (e.g., "ON", "OFF", "TOGGLE")
            logged_at: Timestamp of the action (defaults to now)
        
        Returns:
            ControlLog object with the saved data
        """
        if logged_at is None:
            logged_at = datetime.utcnow()
        
        try:
            data: ControlLog = {
                "device_id": device_id,
                "user_id": user_id,
                "action": action,
                "logged_at": logged_at.isoformat(),
            }
            
            result = self._supabase.insert("control_logs", data)
            logger.info(
                f"[REPO] Saved control log: device_id={device_id}, "
                f"user_id={user_id}, action={action}"
            )
            return result
        except Exception as e:
            logger.error(f"[REPO] Failed to save control log: {str(e)}")
            raise
    
    def get_recent_sensor_readings(
        self,
        sensor_id: int,
        limit: int = 100
    ) -> List[SensorReading]:
        """
        Retrieve recent sensor readings for a specific sensor
        
        Args:
            sensor_id: ID of the sensor
            limit: Maximum number of readings to return
        
        Returns:
            List of SensorReading objects
        """
        try:
            # Fetch from Supabase with ordering by timestamp (descending)
            results = self._supabase.select(
                "sensor_data",
                filters={"sensor_id": sensor_id}
            )
            # Sort by logged_at descending and limit
            results_sorted = sorted(
                results,
                key=lambda x: x.get("logged_at", ""),
                reverse=True
            )[:limit]
            logger.info(f"[REPO] Retrieved {len(results_sorted)} readings for sensor {sensor_id}")
            return results_sorted
        except Exception as e:
            logger.error(f"[REPO] Failed to get sensor readings: {str(e)}")
            raise
    
    def get_control_logs(
        self,
        device_id: Optional[int] = None,
        limit: int = 100
    ) -> List[ControlLog]:
        """
        Retrieve control logs, optionally filtered by device_id
        
        Args:
            device_id: Optional device ID to filter by
            limit: Maximum number of logs to return
        
        Returns:
            List of ControlLog objects
        """
        try:
            filters = {"device_id": device_id} if device_id else None
            results = self._supabase.select("control_logs", filters=filters) if filters else self._supabase.select("control_logs")
            
            # Sort by logged_at descending and limit
            results_sorted = sorted(
                results,
                key=lambda x: x.get("logged_at", ""),
                reverse=True
            )[:limit]
            logger.info(f"[REPO] Retrieved {len(results_sorted)} control logs")
            return results_sorted
        except Exception as e:
            logger.error(f"[REPO] Failed to get control logs: {str(e)}")
            raise
    
    def save_alert(
        self,
        threshold_id: int,
        start_time: Optional[datetime] = None,
        is_resolved: bool = False
    ) -> AlertEvent:
        """
        Save an alert event to the database
        
        Args:
            threshold_id: ID of the threshold that was exceeded
            start_time: When the alert started (defaults to now)
            is_resolved: Whether the alert has been resolved
        
        Returns:
            AlertEvent object with the saved data
        """
        if start_time is None:
            start_time = datetime.utcnow()
        
        try:
            data: AlertEvent = {
                "threshold_id": threshold_id,
                "start_time": start_time.isoformat(),
                "end_time": None,
                "is_resolved": is_resolved,
            }
            
            result = self._supabase.insert("alerts", data)
            logger.info(
                f"[REPO] Saved alert: threshold_id={threshold_id}, "
                f"resolved={is_resolved}"
            )
            return result
        except Exception as e:
            logger.error(f"[REPO] Failed to save alert: {str(e)}")
            raise
    
    def resolve_alert(
        self,
        alert_id: int,
        end_time: Optional[datetime] = None
    ) -> None:
        """
        Mark an alert as resolved
        
        Args:
            alert_id: ID of the alert to resolve
            end_time: When the alert ended (defaults to now)
        """
        if end_time is None:
            end_time = datetime.utcnow()
        
        try:
            data = {
                "is_resolved": True,
                "end_time": end_time.isoformat(),
            }
            self._supabase.update("alerts", data, {"alert_id": alert_id})
            logger.info(f"[REPO] Resolved alert: alert_id={alert_id}")
        except Exception as e:
            logger.error(f"[REPO] Failed to resolve alert: {str(e)}")
            raise
