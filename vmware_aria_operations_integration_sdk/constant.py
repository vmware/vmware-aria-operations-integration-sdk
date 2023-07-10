#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import os
from os import environ
from os import path
from sys import platform

VERSION_FILE = "container_versions.json"
CONTAINER_BASE_NAME = "base-adapter"
CONTAINER_REGISTRY_PATH = "vmware_aria_operations_integration_sdk"
CONTAINER_REGISTRY_HOST = "projects.registry.vmware.com"

if platform == "win32":
    CONFIG_DIRECTORY = path.join(
        environ.get("LocalAppData", ""), "VMware", "Aria Operations Integration SDK"
    )
else:
    CONFIG_DIRECTORY = path.join(
        environ.get("HOME", ""), ".vmware-aria-operations-integration-sdk"
    )

try:
    os.makedirs(CONFIG_DIRECTORY, exist_ok=True)
except OSError as e:
    # This should rarely if ever happen
    print(
        f"Could not create config directory '{CONFIG_DIRECTORY}'. Please manually create and rerun this command."
    )
    print(f"Error: {e}")
    exit(1)

GLOBAL_CONFIG_FILE = path.join(CONFIG_DIRECTORY, "config.json")
CONFIG_CONTAINER_REGISTRY_KEY = "container_registry"
CONFIG_FALLBACK_CONTAINER_REGISTRY_KEY = "docker_registry"
CONFIG_DEFAULT_MEMORY_LIMIT_KEY = "default_memory_limit"
CONFIG_DEFAULT_CONTAINER_REGISTRY_PATH_KEY = "default_container_registry_path"
CONFIG_PROJECTS_PATH_KEY = "projects"
CONFIG_SUITE_API_HOSTNAME_KEY = "suite_api_hostname"
CONFIG_SUITE_API_USERNAME_KEY = "suite_api_username"
CONFIG_SUITE_API_PASSWORD_KEY = "suite_api_password"
DEFAULT_MEMORY_LIMIT = 1024
DEFAULT_PORT = 8080
REPO_NAME = "vmware-aria-operations-integration-sdk"
REPOSITORY_LOCATION = "repository_location"
COLLECT_ENDPOINT = "collect"
CONNECT_ENDPOINT = "test"
ENDPOINTS_URLS_ENDPOINT = "endpointURLs"
ADAPTER_DEFINITION_ENDPOINT = "adapterDefinition"
API_VERSION_ENDPOINT = "apiVersion"

# CLI options keys
SAMPLE_ADAPTER_OPTION_KEY = "sample_adapter"
NEW_ADAPTER_OPTION_KEY = "new_adapter"
