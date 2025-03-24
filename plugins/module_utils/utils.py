import logging
import sys


def makeSimpleLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s] [%(name)s] %(message)s'))
    logger.addHandler(handler)
    return logger
