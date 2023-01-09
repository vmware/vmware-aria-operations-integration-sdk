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
from typing import Tuple

from vmware_aria_operations_integration_sdk.config import get_config_value
from vmware_aria_operations_integration_sdk.config import set_config_value
from vmware_aria_operations_integration_sdk.constant import DEFAULT_MEMORY_LIMIT
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
        certificates: Optional[List[str]] = None,
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
    def extract(cls, json_connection: Dict) -> Connection:
        name = json_connection["name"]
        identifiers = json_connection["identifiers"]
        credential = json_connection["credential"]
        certificates = json_connection.get("certificates", None)
        hostname = json_connection.get("suite_api_hostname", None)
        username = json_connection.get("suite_api_username", None)
        password = json_connection.get("suite_api_password", None)
        return Connection(
            name, identifiers, credential, certificates, (hostname, username, password)
        )


class Project:
    def __init__(
        self,
        path: str,
        connections: Optional[List[Connection]] = None,
        docker_port: int = 8080,
    ) -> None:
        if connections is None:
            connections = []
        self.path = os.path.abspath(path)
        self.connections = connections
        self.docker_port = docker_port

    def name(self) -> str:
        return get_project_name(self.path)

    def record(self) -> None:
        config_file = os.path.join(self.path, "config.json")
        set_config_value(
            "connections", [conn.__dict__ for conn in self.connections], config_file
        )
        set_config_value("docker_port", self.docker_port, config_file)

    @classmethod
    def extract(cls, path: str) -> Project:
        local_config_file = os.path.join(path, "config.json")
        if not os.path.isfile(local_config_file):
            with open(local_config_file, "w") as config:
                json.dump({}, config, indent=4, sort_keys=True)

        with open(local_config_file, "r") as config:
            json_config = json.load(config)
            connections = [
                Connection.extract(connection)
                for connection in json_config.get("connections", [])
            ]
            docker_port = json_config.get("docker_port", 8080)
            return Project(path, connections, docker_port)


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
    project_paths: List[str] = get_config_value("projects", [])
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
    project_paths: Set[str] = set(get_config_value("projects", []))  # type: ignore
    project_paths.add(path)
    set_config_value(
        "projects",
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
