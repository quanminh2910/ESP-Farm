from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from config.settings import Settings
from services.sensor_data_repository import SensorDataRepository
from services.serial_service import SerialService
from utils.logger import get_logger

logger = get_logger(__name__)


def _sensor_id_from_key(key: str) -> int | None:
    if key == "TEMP":
        return Settings.TEMPERATURE_SENSOR_ID
    if key == "HUMIDITY":
        return Settings.HUMIDITY_SENSOR_ID
    if key == "SOIL":
        return Settings.SOIL_SENSOR_ID
    return None


async def _serial_ingest_worker(app: FastAPI) -> None:
    serial_service: SerialService = app.state.serial_service
    repository: SensorDataRepository = app.state.sensor_repository
    stop_event: asyncio.Event = app.state.stop_event

    logger.info("[BRIDGE] Serial ingest worker started")
    while not stop_event.is_set():
        try:
            parsed = await asyncio.to_thread(serial_service.read_parsed_sensor_frame)
            if parsed:
                key = parsed["key"]
                value = parsed["value"]
                sensor_id = _sensor_id_from_key(key)

                if sensor_id is None:
                    logger.warning("[BRIDGE] No sensor_id mapping found for key: %s", key)
                else:
                    repository.save_sensor_reading(sensor_id=sensor_id, value=value)
        except Exception as exc:
            logger.error("[BRIDGE] Serial ingest error: %s", exc)

        await asyncio.sleep(0.05)

    logger.info("[BRIDGE] Serial ingest worker stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sensor_repository = SensorDataRepository()
    app.state.serial_service = SerialService()
    app.state.stop_event = asyncio.Event()

    # Best-effort connect; worker will keep reconnecting if unavailable.
    app.state.serial_service.connect()

    worker = asyncio.create_task(_serial_ingest_worker(app))
    app.state.worker_task = worker

    try:
        yield
    finally:
        app.state.stop_event.set()
        try:
            await asyncio.wait_for(worker, timeout=3)
        except asyncio.TimeoutError:
            worker.cancel()
        app.state.serial_service.disconnect()


app = FastAPI(
    title="YoloFarm FastAPI Bridge",
    description="Bridge service between MQTT, Supabase/PostgreSQL, and Yolobit Serial",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=Settings.FASTAPI_HOST,
        port=Settings.FASTAPI_PORT,
        reload=False,
    )
