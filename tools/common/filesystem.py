#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import os
import shutil
import zipfile

from . import constant, repository
from .ui import path_prompt, print_formatted as print
from .validation.input_validators import RepoValidator


def get_absolute_project_directory(*path: [str]):
    root_directory = get_root_directory()
    return os.path.abspath(os.path.join(root_directory, *path))


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


def ask_for_repo_path():
    try:
        print(f"The path to the '{constant.REPO_NAME}' repository must be set in the '{constant.GLOBAL_CONFIG_FILE}'\n"
              f"file for this tool to function. It is not currently set.", "class:information", frame=True)
        path = path_prompt(f"Enter path to the '{constant.REPO_NAME}' repository: ", validator=RepoValidator())
        print()
        print()
        return path
    except KeyboardInterrupt:
        print()
        print(f"The path to the '{constant.REPO_NAME}' repository must be present for this tool to function. It can be"
              f"added by manually editing the file '{constant.GLOBAL_CONFIG_FILE}' and adding the path to key '"
              f"{constant.REPOSITORY_LOCATION}', or by running this tool again and entering the path at the prompt.",
              "class:information", frame=True)
        print()
        exit(1)


def get_root_directory(default_path=ask_for_repo_path):
    return repository.get_root_directory(default_path)
