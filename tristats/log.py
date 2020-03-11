import logging
import os


def setup_logger(filename, level=logging.DEBUG):
    formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)s[%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    name = os.path.splitext(filename)[0]
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
