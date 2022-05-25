import json
import os
import shutil
import zipfile

from prompt_toolkit import print_formatted_text as print, prompt
from . import constant, repository
from .constant import REPOSITORY_LOCATION


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
        repo_path = prompt(f"Enter path to the '{constant.REPO_NAME}' repository (type q to quit): ")
        while not os.path.exists(repo_path) and repo_path != "q":
            print(f"{repo_path} is not a valid path")
            repo_path = prompt(f"Enter path to the '{constant.REPO_NAME}' repository (type q to quit): ")

        if repo_path == "q":
            exit_and_prompt()
        return repo_path
    except KeyboardInterrupt:
        print()
        exit_and_prompt()


def exit_and_prompt():
    print(
        f"The path to the '{constant.REPO_NAME}' repository must be present for this tool to function. It can be "
        f"added by manually editing the file '{constant.CONFIG_FILE}' and adding the path to key '"
        f"{REPOSITORY_LOCATION}', or by running this tool again and entering the path at the prompt.")
    exit(1)


def get_root_directory(default_path=ask_for_repo_path):
    return repository.get_root_directory(default_path)
