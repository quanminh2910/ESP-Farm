from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PumpControlRequest(BaseModel):
    action: str = Field(..., description="Pump action: ON or OFF")
    user_id: Optional[int] = Field(None, description="Optional user id for logging")


class PumpControlResponse(BaseModel):
    success: bool
    message: str
    sent_frame: Optional[str] = None


class SensorRecord(BaseModel):
    log_id: Optional[int] = None
    sensor_id: int
    value: float
    logged_at: Optional[datetime] = None


class ControlLogRecord(BaseModel):
    log_id: Optional[int] = None
    device_id: int
    user_id: int
    action: str
    logged_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str
    serial_connected: bool
    database_connected: bool


class MqttWebhookRequest(BaseModel):
    topic: str
    payload: str


class SensorRecordsResponse(BaseModel):
    items: List[SensorRecord]


class ControlLogsResponse(BaseModel):
    items: List[ControlLogRecord]
