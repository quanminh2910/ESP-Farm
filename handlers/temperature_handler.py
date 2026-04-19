from typing import Optional

from handlers.base_handler import BaseHandler
from services.automation_service import TemperatureAutomationService
from services.sensor_data_repository import SensorDataRepository
from config.settings import Settings
from utils.logger import get_logger

logger = get_logger(__name__)

class TemperatureHandler(BaseHandler):
    def __init__(
        self,
        automation_service: Optional[TemperatureAutomationService] = None,
        sensor_repository: Optional[SensorDataRepository] = None,
    ):
        self.automation_service = automation_service or TemperatureAutomationService()
        self.sensor_repository = sensor_repository or SensorDataRepository()

    def update(self, topic: str, payload: str):
        try:
            temp = float(payload)
        except (TypeError, ValueError):
            logger.warning(f"[TEMPERATURE] Invalid payload: {payload}")
            return

        logger.info(f"[TEMPERATURE] Current temperature: {temp}°C")
        
        # Save sensor reading to Supabase
        try:
            self.sensor_repository.save_sensor_reading(
                sensor_id=Settings.TEMPERATURE_SENSOR_ID,
                value=temp
            )
        except Exception as e:
            logger.error(f"[TEMPERATURE] Failed to save reading to database: {str(e)}")
        
        # Process temperature through automation service
        self.automation_service.process_temperature(temp)