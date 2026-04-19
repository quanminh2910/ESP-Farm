from typing import Optional

from config.settings import Settings
from handlers.base_handler import BaseHandler
from services.auth_service import AuthService
from services.farm_service import FarmService
from services.sensor_data_repository import SensorDataRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class LedHandler(BaseHandler):
    def __init__(
        self,
        sensor_repository: Optional[SensorDataRepository] = None,
        auth_service: Optional[AuthService] = None,
    ):
        self.sensor_repository = sensor_repository or SensorDataRepository()
        self.auth_service = auth_service or AuthService()

    def update(self, topic: str, payload: str):
        action = payload.strip().upper()
        if action in {"1", "ON"}:
            FarmService.turn_on_led()
            action = "ON"
        elif action in {"0", "OFF"}:
            FarmService.turn_off_led()
            action = "OFF"
        else:
            logger.warning(f"[LED] Unknown payload: {payload}")
            return

        try:
            user_id = AuthService.get_current_user_id()
            self.sensor_repository.save_control_log(
                device_id=Settings.LED_DEVICE_ID,
                user_id=user_id,
                action=action,
            )
            logger.info(
                f"[LED] Logged control action: device={Settings.LED_DEVICE_ID}, "
                f"action={action}, user={user_id}"
            )
        except Exception as exc:
            logger.error(f"[LED] Failed to log control action: {str(exc)}")
