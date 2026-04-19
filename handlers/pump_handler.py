from typing import Optional

from handlers.base_handler import BaseHandler
from services.farm_service import FarmService
from services.sensor_data_repository import SensorDataRepository
from services.auth_service import AuthService
from config.settings import Settings
from utils.logger import get_logger

logger = get_logger(__name__)


class PumpHandler(BaseHandler):
    def __init__(
        self,
        sensor_repository: Optional[SensorDataRepository] = None,
        auth_service: Optional[AuthService] = None,
    ):
        self.sensor_repository = sensor_repository or SensorDataRepository()
        self.auth_service = auth_service or AuthService()
    
    def update(self, topic: str, payload: str):
        try:
            normalized = payload.strip().upper()

            if normalized in {"1", "ON"}:
                FarmService.turn_on_pump()
                action = "ON"
            elif normalized in {"0", "OFF"}:
                FarmService.turn_off_pump()
                action = "OFF"
            else:
                logger.warning(f"[PUMP] Unknown payload: {payload}")
                return
            
            # Log the control action to Supabase
            try:
                user_id = AuthService.get_current_user_id()
                self.sensor_repository.save_control_log(
                    device_id=Settings.PUMP_DEVICE_ID,
                    user_id=user_id,
                    action=action
                )
                logger.info(
                    f"[PUMP] Logged control action: device={Settings.PUMP_DEVICE_ID}, "
                    f"action={action}, user={user_id}"
                )
            except Exception as e:
                logger.error(f"[PUMP] Failed to log control action: {str(e)}")
        except Exception as e:
            logger.error(f"[PUMP] Handler error: {str(e)}")