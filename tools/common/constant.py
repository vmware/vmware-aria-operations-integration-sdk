import os

VERSION_FILE = "container_versions.json"
CONFIG_DIRECTORY = os.path.join(os.environ.get("HOME"), ".vrops-sdk")
CONFIG_FILE = os.path.join(CONFIG_DIRECTORY, "config.json")
DEFAULT_PORT = 8080
REPO_NAME = "vrops-python-sdk"  # TODO: change the name of the repo
REPOSITORY_LOCATION = "repository_location"
