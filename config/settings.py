import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Adafruit IO Configuration
    AIO_SERVER = "io.adafruit.com"
    AIO_PORT = 1883
    AIO_USERNAME = os.getenv("AIO_USERNAME")
    AIO_KEY = os.getenv("AIO_KEY")
    TEMP_HIGH_THRESHOLD = float(os.getenv("TEMP_HIGH_THRESHOLD", "37"))
    TEMP_LOW_THRESHOLD = float(os.getenv("TEMP_LOW_THRESHOLD", "35"))
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_DB_TIMEOUT = int(os.getenv("SUPABASE_DB_TIMEOUT", "10"))
    
    # Sensor & Device ID Mappings
    # Sensor IDs from your Supabase schema
    TEMPERATURE_SENSOR_ID = int(os.getenv("TEMPERATURE_SENSOR_ID", "1"))
    HUMIDITY_SENSOR_ID = int(os.getenv("HUMIDITY_SENSOR_ID", "2"))
    SOIL_SENSOR_ID = int(os.getenv("SOIL_SENSOR_ID", "3"))
    MOISTURE_SENSOR_ID = int(os.getenv("MOISTURE_SENSOR_ID", os.getenv("SOIL_SENSOR_ID", "3")))
    
    # Device IDs from your Supabase schema
    PUMP_DEVICE_ID = int(os.getenv("PUMP_DEVICE_ID", "1"))
    FAN_DEVICE_ID = int(os.getenv("FAN_DEVICE_ID", "2"))
    LED_DEVICE_ID = int(os.getenv("LED_DEVICE_ID", "3"))
    
    # User ID for system automation actions (no manual user interaction)
    SYSTEM_USER_ID = int(os.getenv("SYSTEM_USER_ID", "1"))

    # FastAPI bridge runtime
    FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
    FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))

    # Serial (Yolobit)
    SERIAL_PORT = os.getenv("SERIAL_PORT", "COM3")
    SERIAL_BAUDRATE = int(os.getenv("SERIAL_BAUDRATE", "115200"))
    SERIAL_TIMEOUT_SEC = float(os.getenv("SERIAL_TIMEOUT_SEC", "1.0"))
    SERIAL_RECONNECT_INTERVAL_SEC = float(os.getenv("SERIAL_RECONNECT_INTERVAL_SEC", "2.0"))