#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import logging
import os
from configparser import ConfigParser
from logging.handlers import RotatingFileHandler
from typing import Optional

log_handler: Optional[RotatingFileHandler] = None


def setup_logging(filename: str, file_count: int = 5, max_size: int = 0) -> None:
    """
    :param filename The name of the file to log to
    :param file_count The total number of files to retain. Defaults to 5.
    :param max_size The maximum size in bytes of each file before the file
                    automatically rotates to a new one. Defaults to '0', which will
                    do no automatic rotation. Requires calling the 'rotate()' function
                    manually to ensure logs do not become too large.
    """
    try:
        global log_handler
        log_handler = RotatingFileHandler(
            os.path.join(os.sep, "var", "log", filename),
            maxBytes=max_size,
            backupCount=file_count,
        )
        logging.basicConfig(
            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=_get_level("DEFAULT"),
            handlers=[log_handler],
        )
    except Exception:
        logging.basicConfig(level=logging.CRITICAL + 1)


def _get_level(name: str, default_level: int = logging.INFO) -> int:
    log_config_file = os.path.join(os.sep, "var", "log", "loglevels.cfg")
    if not os.path.isfile(log_config_file):
        new_config = ConfigParser()
        new_config["DEFAULT"] = {"level": logging.getLevelName(default_level)}
        with open(log_config_file, "w") as config_file:
            new_config.write(config_file)
    config = ConfigParser()
    config.read(log_config_file)
    try:
        if name in config and "level" in config[name]:
            return int(logging.getLevelName(config[name].get("level")))
        elif "DEFAULT" in config:
            return int(
                logging.getLevelName(
                    config["DEFAULT"].get("level", logging.getLevelName(default_level))
                )
            )
        else:
            return default_level
    except ValueError:
        return default_level


def getLogger(name: str, default_level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(_get_level(name, default_level))
    return logger


def rotate() -> None:
    if log_handler:
        log_handler.doRollover()
