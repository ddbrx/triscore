import logging
import os

def setup_logger_from_file(file, level=logging.DEBUG):
    name = os.path.splitext(file)[0]
    return setup_logger(name)

def setup_logger(name, level = logging.DEBUG):
    formatter=logging.Formatter(
        fmt = '%(asctime)s %(levelname)s[%(name)s] %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S')

    handler=logging.StreamHandler()
    handler.setFormatter(formatter)

    logger=logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger
