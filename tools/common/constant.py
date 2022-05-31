import os
from sys import platform

VERSION_FILE = "container_versions.json"
CONFIG_FILE = "vrops_integration_sdk"
CONFIG_DIRECTORY = os.path.join(
    os.environ.get("APPDATA" if platform == "win32" else "HOME"),
    CONFIG_FILE if platform == "win32" else f".{CONFIG_FILE}"
)
CONFIG_FILE = os.path.join(CONFIG_DIRECTORY, "config.json")
DEFAULT_PORT = 8080
REPO_NAME = "vrops-python-sdk"  # TODO: change the name of the repo
REPOSITORY_LOCATION = "repository_location"
