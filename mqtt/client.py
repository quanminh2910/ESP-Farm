from Adafruit_IO import MQTTClient
from config.settings import Settings
from mqtt.topics import Topics
from utils.logger import get_logger

logger = get_logger(__name__)

class MQTTClientSingleton:
    _instance = None        # Protected instance
    #! Singleton instance init
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MQTTClientSingleton, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        logger.info("Initialising Adafruit MQTT Singleton Client")
        self._client = MQTTClient(Settings.AIO_USERNAME, Settings.AIO_KEY)
        self._callback()    # Gateway callback functions
    
    def _callback(self):    # Set AIO MQTT callback functions
        self._client.on_connect = self._connected
        self._client.on_disconnect = self._disconnected
        self._client.on_subscribe = self._subscribe
    
    def _connected(self, client):
        logger.info("[CONNECTED] Successfully connected to Adafruit IO!")
        client.subscribe(Topics.TEMPERATURE)
        client.subscribe(Topics.HUMIDITY)
        client.subscribe(Topics.MOISTURE)
        client.subscribe(Topics.PUMP)
        client.subscribe(Topics.FAN)
        client.subscribe(Topics.LED)
        # client.subscribe(Settings.AIO_FEED_ID)

    def _subscribe(self, client , userdata , mid , granted_qos):
        logger.info("[SUBSCRIBED] Successfully subscribed")
        """
        Do something
        """

    def _disconnected(self,client):
        logger.warning("[DISCONNECTED] Disconnected from Adafruit IO!")

    # Getter
    def get_client(self):
        return self._client
    
    # Start the MQTT client loop
    def connect(self):      # Called from gateway/gateway.py
        self._client.connect()

    def publish(self, feed_ID: str, payload: str):
        logger.info(f"[PUBLISH] Sending to: {feed_ID} with payload: {payload}")
        self._client.publish(feed_ID, payload)