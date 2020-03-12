import logging
import os


def setup_logger(filename, level=logging.DEBUG):
    name = os.path.splitext(os.path.basename(filename))[0]

    formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)s[%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
