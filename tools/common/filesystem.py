import json
import os
import zipfile

from common import constant


def get_absolute_project_directory(*path: [str]):
    root_directory = get_root_directory()
    return os.path.abspath(os.path.join(root_directory, *path))


def mkdir(basepath, *paths):
    path = os.path.join(basepath, *paths)
    if not os.path.exists(path):
        os.mkdir(path, 0o755)
    return path


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


def get_root_directory():
    config_file_path = os.path.join(os.environ.get("HOME"), ".vrops-sdk")

    # Check for config directory
    if not os.path.isdir(config_file_path):
        mkdir(config_file_path)

    # Add the file to the path
    config_file_path = os.path.join(config_file_path, constant.CONFIG_FILE)
    root_directory = ""

    if not os.path.isfile(config_file_path):
        with open(config_file_path, "r") as config:
            root_directory = ask_for_repo_path()
            config_json = {"repository_location": root_directory}
            json.dump(config_json, config, indent=4, sort_keys=True)
    else:
        with open(config_file_path, "r") as config:
            config_json = json.load(config)

        with open(config_file_path, "w") as config:
            # Even if the value exist we have to make sure is still valid
            if "repository_location" in config_json and os.path.exists(config_json["repository_location"]):
                root_directory = config_json["repository_location"]
            else:
                root_directory = ask_for_repo_path()
            config_json["repository_location"] = root_directory
            json.dump(config_json, config, indent=4, sort_keys=True)

    return root_directory


def ask_for_repo_path():
    while not os.path.exists(repo_path := input(f"Enter path to {constant.REPO_NAME} repo(type q to quit): ")):
        print(f"{repo_path} is not a valid path")

    return repo_path
