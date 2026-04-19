from typing import Optional

from config.settings import Settings
from mqtt.client import MQTTClientSingleton
from mqtt.topics import Topics
from utils.logger import get_logger

logger = get_logger(__name__)


class TemperatureAutomationService:
    def __init__(
        self,
        mqtt_client: Optional[MQTTClientSingleton] = None,
        high_threshold: float = Settings.TEMP_HIGH_THRESHOLD,
        low_threshold: float = Settings.TEMP_LOW_THRESHOLD,
        command_topic: str = Topics.PUMP,
    ):
        if low_threshold >= high_threshold:
            raise ValueError("low_threshold must be lower than high_threshold")

        self._mqtt_client = mqtt_client or MQTTClientSingleton()
        self._high_threshold = high_threshold
        self._low_threshold = low_threshold
        self._command_topic = command_topic
        self._pump_on = False

    def process_temperature(self, temperature: float):
        if temperature > self._high_threshold and not self._pump_on:
            self._mqtt_client.publish(self._command_topic, "ON")
            self._pump_on = True
            logger.warning(
                "[AUTOMATION] Temperature %.2f > %.2f. Sent command: ON",
                temperature,
                self._high_threshold,
            )
            return

        if temperature < self._low_threshold and self._pump_on:
            self._mqtt_client.publish(self._command_topic, "OFF")
            self._pump_on = False
            logger.info(
                "[AUTOMATION] Temperature %.2f < %.2f. Sent command: OFF",
                temperature,
                self._low_threshold,
            )
