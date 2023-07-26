#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import logging
import os
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

from vmware_aria_operations_integration_sdk.config import get_config_value
from vmware_aria_operations_integration_sdk.config import set_config_value
from vmware_aria_operations_integration_sdk.constant import CONFIG_FILE_NAME
from vmware_aria_operations_integration_sdk.constant import CONFIG_PROJECTS_PATH_KEY
from vmware_aria_operations_integration_sdk.constant import (
    CONNECTIONS_CONFIG_CONNECTION_CERTIFICATES_KEY,
)
from vmware_aria_operations_integration_sdk.constant import (
    CONNECTIONS_CONFIG_CONNECTION_CREDENTIAL_KEY,
)
from vmware_aria_operations_integration_sdk.constant import (
    CONNECTIONS_CONFIG_CONNECTION_IDENTIFIERS_KEY,
)
from vmware_aria_operations_integration_sdk.constant import (
    CONNECTIONS_CONFIG_CONNECTION_NAME_KEY,
)
from vmware_aria_operations_integration_sdk.constant import (
    CONNECTIONS_CONFIG_CONNECTIONS_LIST_KEY,
)
from vmware_aria_operations_integration_sdk.constant import (
    CONNECTIONS_CONFIG_SUITE_API_HOSTNAME_KEY,
)
from vmware_aria_operations_integration_sdk.constant import (
    CONNECTIONS_CONFIG_SUITE_API_PASSWORD_KEY,
)
from vmware_aria_operations_integration_sdk.constant import (
    CONNECTIONS_CONFIG_SUITE_API_USERNAME_KEY,
)
from vmware_aria_operations_integration_sdk.constant import CONNECTIONS_FILE_NAME
from vmware_aria_operations_integration_sdk.constant import DEFAULT_MEMORY_LIMIT
from vmware_aria_operations_integration_sdk.constant import (
    DEFAULT_PLACEHOLDER_SUITE_API_HOSTNAME,
)
from vmware_aria_operations_integration_sdk.constant import (
    DEFAULT_PLACEHOLDER_SUITE_API_PASSWORD,
)
from vmware_aria_operations_integration_sdk.constant import (
    DEFAULT_PLACEHOLDER_SUITE_API_USERNAME,
)
from vmware_aria_operations_integration_sdk.logging_format import CustomFormatter
from vmware_aria_operations_integration_sdk.logging_format import PTKHandler
from vmware_aria_operations_integration_sdk.propertiesfile import load_properties
from vmware_aria_operations_integration_sdk.ui import path_prompt
from vmware_aria_operations_integration_sdk.ui import selection_prompt
from vmware_aria_operations_integration_sdk.validation.input_validators import (
    ProjectValidator,
)

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = PTKHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)


class Connection:
    def __init__(
        self,
        name: str,
        identifiers: Dict[str, Any],
        credential: Dict[str, Any],
        certificates: Optional[List[Dict]] = None,
        suite_api_connection: Tuple[Optional[str], Optional[str], Optional[str]] = (
            None,
            None,
            None,
        ),
    ) -> None:
        self.name = name
        self.identifiers = identifiers
        self.credential = credential
        self.certificates = certificates
        self.suite_api_hostname = suite_api_connection[0]
        self.suite_api_username = suite_api_connection[1]
        self.suite_api_password = suite_api_connection[2]
        self.custom_collection_number: Optional[int] = None
        self.custom_collection_window: Optional[object] = None

    def get_memory_limit(self) -> int:
        memory_limit = self.identifiers.get(
            "container_memory_limit", DEFAULT_MEMORY_LIMIT
        )
        if type(memory_limit) is dict:
            memory_limit = memory_limit.get("value", DEFAULT_MEMORY_LIMIT)

        try:
            memory_limit = int(memory_limit)
            if memory_limit < 6:
                logger.warning(
                    f"'container_memory_limit' of {memory_limit} MB is below the 6MB docker limit."
                )
                logger.warning(f"Using minimum value: 6 MB")
                memory_limit = 6
        except ValueError as e:
            logger.warning(f"Cannot set 'container_memory_limit': {e}")
            logger.warning(f"Using default value: {DEFAULT_MEMORY_LIMIT} MB")
            memory_limit = DEFAULT_MEMORY_LIMIT
        return memory_limit  # type: ignore

    @classmethod
    def extract(cls, path: str, json_connection: Dict) -> Connection:
        name = json_connection[CONNECTIONS_CONFIG_CONNECTION_NAME_KEY]
        identifiers = json_connection[CONNECTIONS_CONFIG_CONNECTION_IDENTIFIERS_KEY]
        credential = json_connection[CONNECTIONS_CONFIG_CONNECTION_CREDENTIAL_KEY]
        certificates = json_connection.get(
            CONNECTIONS_CONFIG_CONNECTION_CERTIFICATES_KEY, None
        )

        default_hostname = get_config_value(
            CONNECTIONS_CONFIG_SUITE_API_HOSTNAME_KEY,
            DEFAULT_PLACEHOLDER_SUITE_API_HOSTNAME,
            os.path.join(path, CONNECTIONS_FILE_NAME),
        )
        default_username = get_config_value(
            CONNECTIONS_CONFIG_SUITE_API_USERNAME_KEY,
            DEFAULT_PLACEHOLDER_SUITE_API_USERNAME,
            os.path.join(path, CONNECTIONS_FILE_NAME),
        )
        default_password = get_config_value(
            CONNECTIONS_CONFIG_SUITE_API_PASSWORD_KEY,
            DEFAULT_PLACEHOLDER_SUITE_API_PASSWORD,
            os.path.join(path, CONNECTIONS_FILE_NAME),
        )

        hostname = (
            json_connection.get(CONNECTIONS_CONFIG_SUITE_API_HOSTNAME_KEY)
            or default_hostname
        )
        username = (
            json_connection.get(CONNECTIONS_CONFIG_SUITE_API_USERNAME_KEY)
            or default_username
        )
        password = (
            json_connection.get(CONNECTIONS_CONFIG_SUITE_API_PASSWORD_KEY)
            or default_password
        )

        return Connection(
            name, identifiers, credential, certificates, (hostname, username, password)
        )


class Project:
    def __init__(
        self,
        path: str,
        connections: Optional[List[Connection]] = None,
    ) -> None:
        if connections is None:
            connections = []
        self.path = os.path.abspath(path)
        self.connections = connections

    def name(self) -> str:
        return get_project_name(self.path)

    def record(self) -> None:
        connections_file = os.path.join(self.path, CONNECTIONS_FILE_NAME)
        set_config_value(
            CONNECTIONS_CONFIG_CONNECTIONS_LIST_KEY,
            [conn.__dict__ for conn in self.connections],
            connections_file,
        )

    @classmethod
    def extract(cls, path: str) -> Project:
        local_config_file = os.path.join(path, CONFIG_FILE_NAME)
        connections_file = os.path.join(path, CONNECTIONS_FILE_NAME)

        if not os.path.isfile(local_config_file):
            with open(local_config_file, "w") as _config:
                json.dump({}, _config, indent=4, sort_keys=True)

        # migration logic from 0.* to 1.0 release
        _migrate_connection_file(path, local_config_file, connections_file)

        if not os.path.isfile(connections_file):
            with open(connections_file, "w") as _connections:
                json.dump({}, _connections, indent=4, sort_keys=True)

        with open(connections_file, "r") as _connections:
            json_config = json.load(_connections)
            connections = [
                Connection.extract(path, connection)
                for connection in json_config.get(
                    CONNECTIONS_CONFIG_CONNECTIONS_LIST_KEY, []
                )
            ]

        return Project(path, connections)


def get_project_name(path: str) -> str:
    manifest_resources = os.path.join(path, "resources", "resources.properties")
    if os.path.isfile(manifest_resources):
        properties = load_properties(manifest_resources)
        return properties.get("DISPLAY_NAME", path)
    else:
        return path


def get_project(arguments: Any) -> Project:
    # If a path is supplied, use it first
    path = arguments.path
    if ProjectValidator.is_project_dir(path):
        return _find_project_by_path(path)

    # Otherwise, check if the current directory is a project
    if ProjectValidator.is_project_dir(os.getcwd()):
        return _find_project_by_path(os.getcwd())

    # Finally, prompt the user for the project
    project_paths: List[str] = get_config_value(CONFIG_PROJECTS_PATH_KEY, [])
    path = selection_prompt(
        "Select a project: ",
        [
            (path, get_project_name(path))
            for path in project_paths
            if ProjectValidator.is_project_dir(path)
        ]
        + [("Other", "Other")],
    )
    if path == "Other":
        path = path_prompt(
            "Enter the path to the project: ", validator=ProjectValidator()
        )

    return _find_project_by_path(path)


def record_project(project: Project) -> Project:
    _add_and_update_project_paths(project.path)
    project.record()
    return project


def read_project(path: str) -> Project:
    return Project.extract(path)


def _find_project_by_path(path: str) -> Project:
    path = os.path.abspath(path)
    _add_and_update_project_paths(path)
    return read_project(path)


def _add_and_update_project_paths(path: str) -> None:
    project_paths: Set[str] = set(get_config_value(CONFIG_PROJECTS_PATH_KEY, []))
    project_paths.add(path)
    set_config_value(
        CONFIG_PROJECTS_PATH_KEY,
        sorted(
            list(
                [
                    path
                    for path in project_paths
                    if ProjectValidator.is_project_dir(path)
                ]
            )
        ),
    )


def _migrate_connection_file(
    path: str,
    local_config_file: str,
    connections_file: str,
) -> None:
    connections_data = {}
    connection_file_exists = os.path.isfile(connections_file)
    connection_file_element_keys = [
        CONNECTIONS_CONFIG_SUITE_API_HOSTNAME_KEY,
        CONNECTIONS_CONFIG_SUITE_API_USERNAME_KEY,
        CONNECTIONS_CONFIG_SUITE_API_PASSWORD_KEY,
        CONNECTIONS_CONFIG_CONNECTIONS_LIST_KEY,
    ]

    with open(local_config_file, "r+") as _config:
        json_config = json.load(_config)

        for element in connection_file_element_keys:
            if element in json_config:
                connections_data[element] = json_config.get(element)

        if len(connections_data):
            if not connection_file_exists and selection_prompt(
                f"Found '{CONNECTIONS_FILE_NAME}' elements in '{CONFIG_FILE_NAME}', would you like to "
                f"migrate them?",
                [(True, "Yes"), (False, "No")],
                description="If 'Yes' is selected, all elements will be migrated into"
                f" {CONNECTIONS_FILE_NAME}.\n"
                f"If 'No' is selected, then a new {CONNECTIONS_FILE_NAME} file will be created,"
                " but the connection related "
                f"elements will remain in the {CONFIG_FILE_NAME}.\n"
                "To learn more about connection config file migration, visit\n"
                f"https://vmware.github.io/vmware-aria-operations-integration-sdk"
                f"/troubleshooting_and_faq/other"
                f"/#how-do-i-migrate-connection-related-elements-from-configjson-to-connectionsjson",
            ):
                logger.info(
                    f"Deleting connection-related elements from {CONFIG_FILE_NAME}"
                )
                for element in connections_data:
                    del json_config[element]

                _config.seek(0)
                json.dump(json_config, _config, indent=4, sort_keys=True)
                _config.truncate()

                with open(connections_file, "w") as _connections:
                    json.dump(connections_data, _connections, indent=4, sort_keys=True)

                    _safe_append_to_gitignore(
                        os.path.join(path, ".gitignore"), CONNECTIONS_FILE_NAME
                    )


def _safe_append_to_gitignore(gitignore_file_path: str, token: str) -> None:
    try:
        with open(gitignore_file_path, "r") as gitignore:
            for line in gitignore.readlines():
                if token == line.strip("\n"):
                    return

        with open(gitignore_file_path, "a") as gitignore:
            gitignore.write(f"{token}\n")

        logger.info(f"Appended '{token}' to .gitignore")
    except FileNotFoundError:
        logger.warning(
            f"Could not automatically set the file '{token}' to be ignored in version control."
        )
