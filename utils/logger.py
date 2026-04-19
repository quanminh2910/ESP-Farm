import logging

def get_logger(__name__: str, level=logging.INFO):
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    # Avoid duplicate loggers
    if not logger.handlers:
        handler = logging.StreamHandler()
        format = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
        handler.setFormatter(format)
        logger.addHandler(handler)
    return logger