from __future__ import annotations

import re
import threading
import time
from typing import Dict, Optional, Tuple

import serial
from serial import SerialException

from config.settings import Settings
from utils.logger import get_logger

logger = get_logger(__name__)

FRAME_PATTERN = re.compile(r"^!([A-Z_]+):([-+]?[0-9]*\.?[0-9]+)#$")
VALID_SENSOR_KEYS = {"TEMP", "SOIL", "HUMIDITY"}


class SerialService:
    """Owns serial port lifecycle and frame parsing for Yolobit communication."""

    def __init__(
        self,
        port: str = Settings.SERIAL_PORT,
        baudrate: int = Settings.SERIAL_BAUDRATE,
        timeout: float = Settings.SERIAL_TIMEOUT_SEC,
        reconnect_interval: float = Settings.SERIAL_RECONNECT_INTERVAL_SEC,
    ) -> None:
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._reconnect_interval = reconnect_interval
        self._last_connect_attempt = 0.0
        self._ser: Optional[serial.Serial] = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
        with self._lock:
            if self._ser and self._ser.is_open:
                return True

            now = time.time()
            if now - self._last_connect_attempt < self._reconnect_interval:
                return False

            self._last_connect_attempt = now
            try:
                self._ser = serial.Serial(
                    port=self._port,
                    baudrate=self._baudrate,
                    timeout=self._timeout,
                )
                logger.info("[SERIAL] Connected to %s @ %s", self._port, self._baudrate)
                return True
            except SerialException as exc:
                logger.warning("[SERIAL] Connect failed on %s: %s", self._port, exc)
                self._ser = None
                return False

    def disconnect(self) -> None:
        with self._lock:
            if self._ser and self._ser.is_open:
                self._ser.close()
                logger.info("[SERIAL] Disconnected from %s", self._port)
            self._ser = None

    def is_connected(self) -> bool:
        return bool(self._ser and self._ser.is_open)

    def send_frame(self, frame: str) -> bool:
        with self._lock:
            if not self._ser or not self._ser.is_open:
                return False
            try:
                self._ser.write(frame.encode("ascii"))
                self._ser.flush()
                logger.info("[SERIAL] Sent frame: %s", frame)
                return True
            except SerialException as exc:
                logger.error("[SERIAL] Send failed: %s", exc)
                self._ser = None
                return False

    def send_pump_command(self, action: str) -> Tuple[bool, str]:
        normalized = action.strip().upper()
        if normalized not in {"ON", "OFF"}:
            return False, "Invalid action. Use ON or OFF"

        if not self.is_connected() and not self.connect():
            return False, "Serial port is not connected"

        frame = f"!PUMP:{normalized}#"
        if not self.send_frame(frame):
            return False, "Failed to send command over serial"

        return True, frame

    def read_raw_line(self) -> Optional[str]:
        with self._lock:
            if not self._ser or not self._ser.is_open:
                return None
            try:
                raw = self._ser.readline()
                if not raw:
                    return None
                line = raw.decode("ascii", errors="ignore").strip()
                return line or None
            except SerialException as exc:
                logger.warning("[SERIAL] Read failed: %s", exc)
                self._ser = None
                return None

    @staticmethod
    def parse_sensor_frame(frame: str) -> Optional[Dict[str, float]]:
        match = FRAME_PATTERN.match(frame)
        if not match:
            return None

        key, value_raw = match.groups()
        if key not in VALID_SENSOR_KEYS:
            return None

        try:
            value = float(value_raw)
        except ValueError:
            return None

        return {"key": key, "value": value}

    def read_parsed_sensor_frame(self) -> Optional[Dict[str, float]]:
        if not self.is_connected() and not self.connect():
            return None

        raw = self.read_raw_line()
        if not raw:
            return None

        parsed = self.parse_sensor_frame(raw)
        if not parsed:
            logger.warning("[SERIAL] Ignored malformed/unsupported frame: %s", raw)
            return None

        logger.info("[SERIAL] Received frame: %s", raw)
        return parsed
