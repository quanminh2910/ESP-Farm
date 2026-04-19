from typing import Optional

from config.settings import Settings
from handlers.base_handler import BaseHandler
from services.sensor_data_repository import SensorDataRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class HumidityHandler(BaseHandler):
    def __init__(self, sensor_repository: Optional[SensorDataRepository] = None):
        self.sensor_repository = sensor_repository or SensorDataRepository()

    def update(self, topic: str, payload: str):
        try:
            humidity = float(payload)
        except (TypeError, ValueError):
            logger.warning(f"[HUMIDITY] Invalid payload: {payload}")
            return

        logger.info(f"[HUMIDITY] Current humidity: {humidity}%")

        try:
            self.sensor_repository.save_sensor_reading(
                sensor_id=Settings.HUMIDITY_SENSOR_ID,
                value=humidity,
            )
        except Exception as exc:
            logger.error(f"[HUMIDITY] Failed to save reading to database: {str(exc)}")
