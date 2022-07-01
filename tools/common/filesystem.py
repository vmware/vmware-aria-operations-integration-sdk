import os
import shutil
import zipfile

from prompt_toolkit import print_formatted_text as print, prompt

from . import constant, repository
from .ui import path_prompt
from .validators import RepoValidator


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
        print(f"The path to the '{constant.REPO_NAME}' repository must be set in the '{constant.CONFIG_FILE}' file ")
        print(f"for this tool to function. It is not currently set.")
        path = path_prompt(f"Enter path to the '{constant.REPO_NAME}' repository: ", validator=RepoValidator())
        print()
        print()
        return path
    except KeyboardInterrupt:
        print()
        print(f"The path to the '{constant.REPO_NAME}' repository must be present for this tool to function. It can be")
        print("added by manually editing the file '{constant.CONFIG_FILE}' and adding the path to key '")
        print("{REPOSITORY_LOCATION}', or by running this tool again and entering the path at the prompt.")
        print()
        exit(1)


def get_root_directory(default_path=ask_for_repo_path):
    return repository.get_root_directory(default_path)
