import os
import appdirs

PRODUCT_NAME = "vROps Integration SDK"
VERSION_FILE = "container_versions.json"
CONFIG_DIRECTORY = os.path.join(appdirs.user_config_dir(PRODUCT_NAME))
CONFIG_FILE = os.path.join(CONFIG_DIRECTORY, "config.json")
DEFAULT_PORT = 8080
REPO_NAME = "vrops-python-sdk"  # TODO: change the name of the repo
REPOSITORY_LOCATION = "repository_location"
