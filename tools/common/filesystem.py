import json
import os
import zipfile

from . import constant


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


def ask_for_repo_path():
    try:
        while not os.path.exists(repo_path := input(f"Enter path to {constant.REPO_NAME} repo(type q to quit): ")) \
                and repo_path != "q":
            print(f"{repo_path} is not a valid path")

        if repo_path == "q":
            return "No repo name given"
    except KeyboardInterrupt:
        print()
        return "No repo name given"

    return repo_path


def get_root_directory(default_path=ask_for_repo_path):
    config_file_path = os.path.join(os.environ.get("HOME"), ".vrops-sdk")

    # Check for config directory
    if not os.path.isdir(config_file_path):
        mkdir(config_file_path)

    # Add the file to the path
    config_file_path = os.path.join(config_file_path, constant.CONFIG_FILE)
    root_directory = ""

    if not os.path.isfile(config_file_path):
        root_directory = default_path()
        with open(config_file_path, "r") as config:
            config_json = {"repository_location": root_directory}
            json.dump(config_json, config, indent=4, sort_keys=True)
    else:
        with open(config_file_path, "r") as config:
            config_json = json.load(config)

        if "repository_location" in config_json and os.path.exists(config_json["repository_location"]):
            root_directory = config_json["repository_location"]
        else:
            root_directory = default_path()

        with open(config_file_path, "w") as config:
            # Even if the value exist we have to make sure is still valid
            config_json["repository_location"] = root_directory
            json.dump(config_json, config, indent=4, sort_keys=True)

    return root_directory
