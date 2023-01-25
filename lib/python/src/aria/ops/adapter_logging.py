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
            level=_get_default_log_level(),
            handlers=[log_handler],
        )
        _set_log_levels()
    except Exception:
        logging.basicConfig(level=logging.CRITICAL + 1)


def _get_default_log_level(default_level: int = logging.INFO) -> int:
    default_level_name = logging.getLevelName(default_level)
    log_config_file = os.path.join(os.sep, "var", "log", "loglevels.cfg")
    config = ConfigParser()
    if os.path.isfile(log_config_file):
        config.read(log_config_file)
    modified = False
    if "adapter" not in config["DEFAULT"]:
        modified = True
        config["DEFAULT"].update({"adapter": default_level_name})
    if "adapter" not in config:
        modified = True
        config["adapter"] = {
            "__main__": default_level_name,
        }
    if modified:
        with open(log_config_file, "w") as config_file:
            config.write(config_file)
    try:
        return int(
            logging.getLevelName(config["DEFAULT"].get("adapter", default_level_name))
        )
    except ValueError:
        return default_level


def _set_log_levels() -> None:
    log_config_file = os.path.join(os.sep, "var", "log", "loglevels.cfg")
    config = ConfigParser()
    config.read(log_config_file)
    for logger in config["adapter"]:
        logging.getLogger(logger).setLevel(config["adapter"][logger])


def getLogger(name: str) -> logging.Logger:
    # convenience function to avoid having to import logging and adapter_logging
    return logging.getLogger(name)


def rotate() -> None:
    """
    Rotates the current adapter logs to their backups (e.g., `adapter.log` to
    `adapter.log.1`) and starts logging to the new adapter.log file.
    :return: None
    """
    if log_handler:
        log_handler.doRollover()
