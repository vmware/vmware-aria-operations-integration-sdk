#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

from os import path, environ
from sys import platform

VERSION_FILE = "container_versions.json"

if platform == "win32":
    CONFIG_DIRECTORY = path.join(environ.get("LocalAppData"), "VMware", "vROps Integration SDK")
else:
    CONFIG_DIRECTORY = path.join(environ.get("HOME"), ".vrops-sdk")

GLOBAL_CONFIG_FILE = path.join(CONFIG_DIRECTORY, "config.json")
DEFAULT_PORT = 8080
REPO_NAME = "vrealize-operations-integration-sdk"
REPOSITORY_LOCATION = "repository_location"
COLLECT_ENDPOINT = "collect"
CONNECT_ENDPOINT = "test"
ENDPOINTS_URLS_ENDPOINT = "endpointURLs"
API_VERSION_ENDPOINT = "apiVersion"
