import os
from sys import platform

VERSION_FILE = "container_versions.json"
CONFIG_DIRECTORY = os.path.join(os.environ.get("HOMEPATH" if platform == "win32" else "HOME"), ".vrops-sdk")
CONFIG_FILE = os.path.join(CONFIG_DIRECTORY, "config.json")
DEFAULT_PORT = 8080
REPO_NAME = "vrops-python-sdk"  # TODO: change the name of the repo
REPOSITORY_LOCATION = "repository_location"
