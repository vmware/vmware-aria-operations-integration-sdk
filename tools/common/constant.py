from os import path, environ
from sys import platform

VERSION_FILE = "container_versions.json"

if platform == "win32":
    CONFIG_DIRECTORY = path.join(environ.get("LocalAppData"), "VMware", "vROps Integration SDK")
else:
    CONFIG_DIRECTORY = path.join(environ.get("HOME"), ".vrops-sdk")

CONFIG_FILE = path.join(CONFIG_DIRECTORY, "config.json")
DEFAULT_PORT = 8080
REPO_NAME = "vrops-python-sdk"  # TODO: change the name of the repo
REPOSITORY_LOCATION = "repository_location"
