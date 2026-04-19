from gateway.gateway import PythonGateway
from handlers.fan_handler import FanHandler
from handlers.humidity_handler import HumidityHandler
from handlers.led_handler import LedHandler
from handlers.moisture_handler import MoistureHandler
from handlers.temperature_handler import TemperatureHandler
from handlers.pump_handler import PumpHandler
from mqtt.topics import Topics
from services.automation_service import TemperatureAutomationService

def main():
    pygateway = PythonGateway()
    automation_service = TemperatureAutomationService(mqtt_client=pygateway.mqtt_ins)

    # Register handlers
    pygateway.register_handler(Topics.TEMPERATURE, TemperatureHandler(automation_service))
    pygateway.register_handler(Topics.HUMIDITY, HumidityHandler())
    pygateway.register_handler(Topics.MOISTURE, MoistureHandler())
    pygateway.register_handler(Topics.PUMP, PumpHandler())
    pygateway.register_handler(Topics.FAN, FanHandler())
    pygateway.register_handler(Topics.LED, LedHandler())

    # Subscribe the feeds
    pygateway.subscribe(Topics.TEMPERATURE)
    pygateway.subscribe(Topics.HUMIDITY)
    pygateway.subscribe(Topics.MOISTURE)
    pygateway.subscribe(Topics.PUMP)
    pygateway.subscribe(Topics.FAN)
    pygateway.subscribe(Topics.LED)

    # Start the MQTT client hehe
    pygateway.start_client()

if __name__ == "__main__":
    main()
