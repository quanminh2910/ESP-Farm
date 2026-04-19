from __future__ import annotations

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, Query, Request

from config.settings import Settings
from models.api_models import (
    ControlLogsResponse,
    HealthResponse,
    MqttWebhookRequest,
    PumpControlRequest,
    PumpControlResponse,
    SensorRecordsResponse,
)
from services.auth_service import AuthService

router = APIRouter()


def _sensor_map() -> Dict[str, int]:
    return {
        "TEMP": Settings.TEMPERATURE_SENSOR_ID,
        "HUMIDITY": Settings.HUMIDITY_SENSOR_ID,
        "SOIL": Settings.SOIL_SENSOR_ID,
    }


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    serial_service = request.app.state.serial_service
    repository = request.app.state.sensor_repository

    serial_connected = serial_service.is_connected() or serial_service.connect()

    database_connected = True
    try:
        repository.get_control_logs(limit=1)
    except Exception:
        database_connected = False

    overall = "ok" if serial_connected and database_connected else "degraded"
    return HealthResponse(
        status=overall,
        serial_connected=serial_connected,
        database_connected=database_connected,
    )


@router.post("/control/pump", response_model=PumpControlResponse)
def control_pump(payload: PumpControlRequest, request: Request) -> PumpControlResponse:
    serial_service = request.app.state.serial_service
    repository = request.app.state.sensor_repository

    success, result = serial_service.send_pump_command(payload.action)
    if not success:
        raise HTTPException(status_code=503, detail=result)

    user_id = payload.user_id if payload.user_id is not None else AuthService.get_current_user_id()

    try:
        repository.save_control_log(
            device_id=Settings.PUMP_DEVICE_ID,
            user_id=user_id,
            action=payload.action.strip().upper(),
            logged_at=datetime.utcnow(),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Command sent but log insert failed: {exc}") from exc

    return PumpControlResponse(success=True, message="Pump command sent", sent_frame=result)


@router.get("/sensor-data/{sensor_id}", response_model=SensorRecordsResponse)
def get_sensor_data(sensor_id: int, request: Request, limit: int = Query(default=20, ge=1, le=500)) -> SensorRecordsResponse:
    repository = request.app.state.sensor_repository
    try:
        records = repository.get_recent_sensor_readings(sensor_id=sensor_id, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read sensor data: {exc}") from exc

    return SensorRecordsResponse(items=records)


@router.get("/control-logs", response_model=ControlLogsResponse)
def get_control_logs(request: Request, limit: int = Query(default=20, ge=1, le=500)) -> ControlLogsResponse:
    repository = request.app.state.sensor_repository
    try:
        logs = repository.get_control_logs(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read control logs: {exc}") from exc

    return ControlLogsResponse(items=logs)


@router.post("/mqtt/webhook")
def mqtt_webhook(payload: MqttWebhookRequest, request: Request) -> dict:
    repository = request.app.state.sensor_repository

    topic = payload.topic.lower().strip()
    mapped_key = None
    if "temp" in topic:
        mapped_key = "TEMP"
    elif "humidity" in topic:
        mapped_key = "HUMIDITY"
    elif "soil" in topic:
        mapped_key = "SOIL"

    if mapped_key is None:
        raise HTTPException(status_code=400, detail="Unsupported topic")

    try:
        sensor_value = float(payload.payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Payload must be numeric") from exc

    sensor_id = _sensor_map()[mapped_key]
    try:
        repository.save_sensor_reading(sensor_id=sensor_id, value=sensor_value)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to persist webhook data: {exc}") from exc

    return {"success": True, "sensor_key": mapped_key, "sensor_id": sensor_id, "value": sensor_value}
