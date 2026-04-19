from typing import Optional

from config.settings import Settings
from handlers.base_handler import BaseHandler
from services.sensor_data_repository import SensorDataRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class MoistureHandler(BaseHandler):
    def __init__(self, sensor_repository: Optional[SensorDataRepository] = None):
        self.sensor_repository = sensor_repository or SensorDataRepository()

    def update(self, topic: str, payload: str):
        try:
            moisture = float(payload)
        except (TypeError, ValueError):
            logger.warning(f"[MOISTURE] Invalid payload: {payload}")
            return

        logger.info(f"[MOISTURE] Current moisture: {moisture}%")

        try:
            self.sensor_repository.save_sensor_reading(
                sensor_id=Settings.MOISTURE_SENSOR_ID,
                value=moisture,
            )
        except Exception as exc:
            logger.error(f"[MOISTURE] Failed to save reading to database: {str(exc)}")
