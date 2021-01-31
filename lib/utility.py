import logging
import random
import sys
from logging import INFO
from logging.handlers import RotatingFileHandler

FORMATTER = logging.Formatter("[%(levelname)s] [%(name)s] - [%(asctime)s]: %(message)s")
LOG_DIR = "logs//"

global log_level


def check_chance(chance):
    return random.random() <= chance


def get_random_array_element(arr):
    idx = round(random.random() * len(arr) - 1)
    return arr[idx]


def get_console_handler(is_system=False):
    if is_system:
        console_handler = logging.StreamHandler(sys.stderr)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler(logger_name):
    file_handler = RotatingFileHandler(LOG_DIR + logger_name + ".log", maxBytes=1024 * 1024, backupCount=10)
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(logger_name, level=INFO, is_system=False):
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.addHandler(get_console_handler(is_system))
    logger.addHandler(get_file_handler(logger_name))
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False
    return logger
