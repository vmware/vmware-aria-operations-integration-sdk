#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import logging
import os
import shutil
import zipfile

from vmware_aria_operations_integration_sdk.src.logging_format import PTKHandler, CustomFormatter

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = PTKHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)


def mkdir(basepath, *paths):
    path = os.path.join(basepath, *paths)
    if not os.path.exists(path):
        os.mkdir(path, 0o755)
    return path


def rm(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        # Nothing to delete
        pass
    except OSError as e:
        logger.warning(f"Could not remove file '{path}': {e}")


def rmdir(basepath, *paths):
    path = os.path.join(basepath, *paths)
    shutil.rmtree(path, ignore_errors=True)


def zip_file(_zip, file):
    _zip.write(file, compress_type=zipfile.ZIP_DEFLATED)


def zip_dir(_zip, directory):
    for file in files_in_directory(directory):
        _zip.write(file, compress_type=zipfile.ZIP_DEFLATED)


def files_in_directory(directory):
    for root, directories, files in os.walk(directory):
        yield root
        for filename in files:
            yield os.path.join(root, filename)

