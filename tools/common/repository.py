import json
import os

from . import constant
from .filesystem import mkdir


def get_root_directory(default_path):
    config_file_path = constant.CONFIG_DIRECTORY

    # Check for config directory
    if not os.path.isdir(config_file_path):
        mkdir(config_file_path)

    # Add the file to the path
    config_file_path = constant.CONFIG_FILE
    root_directory = ""

    if not os.path.isfile(config_file_path):
        root_directory = default_path()
        with open(config_file_path, "w") as config:
            config_json = {constant.REPOSITORY_LOCATION: root_directory}
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
