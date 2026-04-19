import argparse
import random
import time

from config.settings import Settings
from mqtt.client import MQTTClientSingleton
from mqtt.topics import Topics
from utils.logger import get_logger

logger = get_logger(__name__)


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Simulate temperature/humidity data and publish to Adafruit IO feeds"
    )
    parser.add_argument("--interval", type=float, default=2.0, help="Publish interval in seconds")
    parser.add_argument(
        "--spike-every",
        type=int,
        default=6,
        help="Every N ticks, create a temperature spike above high threshold",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Number of ticks to publish. Use 0 for infinite loop",
    )
    return parser


def _generate_values(tick: int, spike_every: int):
    is_spike = spike_every > 0 and tick % spike_every == 0

    if is_spike:
        temperature = round(random.uniform(Settings.TEMP_HIGH_THRESHOLD + 0.6, Settings.TEMP_HIGH_THRESHOLD + 3.0), 2)
        humidity = round(random.uniform(80.0, 92.0), 2)
        mode = "SPIKE"
    else:
        temperature = round(random.uniform(28.0, 34.0), 2)
        humidity = round(random.uniform(55.0, 75.0), 2)
        mode = "NORMAL"

    return mode, temperature, humidity


def main():
    args = _build_parser().parse_args()

    mqtt_client = MQTTClientSingleton()
    mqtt_client.connect()

    tick = 1
    logger.info("[SIM] Started sensor simulation")
    try:
        while True:
            if args.count > 0 and tick > args.count:
                logger.info("[SIM] Reached requested count. Stop simulation.")
                break

            mode, temperature, humidity = _generate_values(tick, args.spike_every)
            mqtt_client.publish(Topics.TEMPERATURE, str(temperature))
            mqtt_client.publish(Topics.HUMIDITY, str(humidity))

            logger.info(
                "[SIM][%s] tick=%s temp=%s humidity=%s",
                mode,
                tick,
                temperature,
                humidity,
            )

            tick += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("[SIM] Stopped by user")


if __name__ == "__main__":
    main()
