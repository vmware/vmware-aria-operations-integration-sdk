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
    Sets up logging using the given parameters.

    Args:
        filename (str): The name of the file to log to.
        file_count (int, optional): The total number of files to retain. Defaults to 5.
        max_size (int, optional): The maximum size in bytes of each file before the file
                                  automatically rotates to a new one. Defaults to '0', which will
                                  do no automatic rotation. Requires calling the 'rotate()' function
                                  manually to ensure logs do not become too large.
    """
    logdir = os.path.join(os.sep, "var", "log")
    if os.access(logdir, os.W_OK):
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
        except Exception as e:
            logging.basicConfig(level=logging.INFO)
            logging.exception(e)
    else:
        logging.basicConfig(level=logging.INFO)
        logging.exception(
            f"Cannot write to log file '{os.path.join(logdir, filename)}'"
        )


def _get_default_log_level(default_level: int = logging.INFO) -> int:
    """
    Retrieves the default logging level from a config file, or returns a default value.

    Args:
        default_level (int, optional): The default logging level if not set in the config file.
                                        Defaults to logging.INFO.

    Returns:
        int: The default logging level.
    """
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
        try:
            with open(log_config_file, "w") as config_file:
                config.write(config_file)
        except Exception as e:
            logging.exception(e)
    try:
        return int(
            logging.getLevelName(config["DEFAULT"].get("adapter", default_level_name))
        )
    except ValueError:
        return default_level


def _set_log_levels() -> None:
    """
    Sets the logging levels for each logger as defined in a config file.
    """
    log_config_file = os.path.join(os.sep, "var", "log", "loglevels.cfg")
    config = ConfigParser()
    if os.path.isfile(log_config_file):
        config.read(log_config_file)
        for logger in config["adapter"]:
            logging.getLogger(logger).setLevel(config["adapter"][logger])


def getLogger(name: str) -> logging.Logger:
    """
    A convenience function to get a logger with a specific name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The requested logger.
    """
    return logging.getLogger(name)


def rotate() -> None:
    """
    Rotates the current adapter logs to their backups (e.g., `adapter.log` to
    `adapter.log.1`) and starts logging to the new adapter.log file.
    """
    if log_handler:
        log_handler.doRollover()
