#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import logging
import os
import shutil
import zipfile
from typing import Callable
from typing import Generator

from vmware_aria_operations_integration_sdk.logging_format import CustomFormatter
from vmware_aria_operations_integration_sdk.logging_format import PTKHandler

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = PTKHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)


def mkdir(basepath: str, *paths: str) -> str:
    path = os.path.join(basepath, *paths)
    if not os.path.exists(path):
        os.mkdir(path, 0o755)
    return path


def rm(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        # Nothing to delete
        pass
    except OSError as e:
        logger.warning(f"Could not remove file '{path}': {e}")


def rmdir(basepath: str, *paths: str) -> None:
    path = os.path.join(basepath, *paths)
    shutil.rmtree(path, ignore_errors=True)


def zip_file(_zip: zipfile.ZipFile, file: str) -> None:
    if os.path.basename(file) == ".gitkeep":
        return
    _zip.write(file, compress_type=zipfile.ZIP_DEFLATED)


def zip_dir(
    _zip: zipfile.ZipFile, directory: str, include_empty_dirs: bool = True
) -> None:
    for file in files_in_directory(directory, include_empty_dirs=include_empty_dirs):
        zip_file(_zip, file)


def files_in_directory(
    directory: str,
    dir_inclusion_func: Callable[[str], bool] = lambda file: True,
    include_empty_dirs: bool = True,
) -> Generator[str, None, None]:
    for root, directories, files in os.walk(directory, topdown=True):
        directories[:] = [
            d for d in directories if dir_inclusion_func(os.path.join(root, d))
        ]
        if files or directories or include_empty_dirs:
            yield root
            for filename in files:
                f = os.path.join(root, filename)
                yield f
