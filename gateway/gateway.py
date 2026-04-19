from mqtt.client import MQTTClientSingleton
from gateway.dispatcher import EventDispatcher
from utils.logger import get_logger

logger = get_logger(__name__)

class PythonGateway:
    def __init__(self):
        self.mqtt_ins = MQTTClientSingleton()
        self.dispatcher = EventDispatcher()

        self.client = self.mqtt_ins.get_client()
        self.client.on_message = self._message

    def _message(self, client, feed_ID: str, payload: str):
        logger.info(f"[MESSAGE] Received from: {feed_ID} with payload: {payload}")
        self.dispatcher.notify(feed_ID, payload)

    def start_client(self):
        self.mqtt_ins.connect()
        logger.info("MQTT connected. Start blocking loop...")
        self.client.loop_blocking()   # giữ process sống để nhận message

    def register_handler(self, feed_ID: str, handler):
        self.dispatcher.register(feed_ID, handler)

    def subscribe(self, feed_ID: str):
        self.client.subscribe(feed_ID)