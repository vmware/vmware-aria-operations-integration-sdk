#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import os
import shutil
import zipfile


def mkdir(basepath, *paths):
    path = os.path.join(basepath, *paths)
    if not os.path.exists(path):
        os.mkdir(path, 0o755)
    return path


def rmdir(basepath, *paths):
    path = os.path.join(basepath, *paths)
    shutil.rmtree(path)


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

