import logging
import random
import sys
from logging import INFO, Logger, StreamHandler
from logging.handlers import RotatingFileHandler
from typing import List, Union

FORMATTER = logging.Formatter("[%(levelname)s] [%(name)s] - [%(asctime)s]: %(message)s")
LOG_DIR = "logs//"

global log_level


def check_chance(chance: float):
    return random.random() <= chance


def get_random_array_element(arr: List):
    idx = round(random.random() * len(arr) - 1)
    return arr[idx]


def get_console_handler(is_system: bool = False) -> StreamHandler:
    if is_system:
        console_handler = StreamHandler(sys.stderr)
    else:
        console_handler = StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler(logger_name: str) -> RotatingFileHandler:
    file_handler = RotatingFileHandler(LOG_DIR + logger_name + ".log", maxBytes=1024 * 1024, backupCount=10,
                                       encoding="utf-8")
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(logger_name: str, level: Union[int, str] = INFO, is_system: bool = False) -> Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.addHandler(get_console_handler(is_system))
    logger.addHandler(get_file_handler(logger_name))
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False
    return logger
