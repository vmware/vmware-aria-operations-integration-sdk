#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
from typing import Optional

from vmware_aria_operations_integration_sdk.src.config import get_config_value, set_config_value
from vmware_aria_operations_integration_sdk.src.constant import DEFAULT_MEMORY_LIMIT
from vmware_aria_operations_integration_sdk.src.logging_format import PTKHandler, CustomFormatter
from vmware_aria_operations_integration_sdk.src.propertiesfile import load_properties
from vmware_aria_operations_integration_sdk.src.ui import selection_prompt, path_prompt
from vmware_aria_operations_integration_sdk.src.validation.input_validators import ProjectValidator

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = PTKHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)


class Connection:
    def __init__(self, name: str,
                 identifiers: dict[str, any],
                 credential: dict[str, any],
                 certificates: Optional[list[str]] = None):
        self.name = name
        self.identifiers = identifiers
        self.credential = credential
        self.certificates = certificates

    def get_memory_limit(self):
        memory_limit = self.identifiers.get("container_memory_limit", DEFAULT_MEMORY_LIMIT)
        if type(memory_limit) is dict:
            memory_limit = memory_limit.get("value", DEFAULT_MEMORY_LIMIT)

        try:
            memory_limit = int(memory_limit)
            if memory_limit < 6:
                logger.warning(f"'container_memory_limit' of {memory_limit} MB is below the 6MB docker limit.")
                logger.warning(f"Using minimum value: 6 MB")
                memory_limit = 6
        except ValueError as e:
            logger.warning(f"Cannot set 'container_memory_limit': {e}")
            logger.warning(f"Using default value: {DEFAULT_MEMORY_LIMIT} MB")
            memory_limit = DEFAULT_MEMORY_LIMIT
        return memory_limit

    @classmethod
    def extract(cls, json_connection):
        name = json_connection["name"]
        identifiers = json_connection["identifiers"]
        credential = json_connection["credential"]
        certificates = json_connection.get("certificates", None)
        return Connection(name, identifiers, credential, certificates)


class Project:
    def __init__(self, path: str, connections: list[Connection] = None, docker_port: int = 8080):
        if connections is None:
            connections = []
        self.path = os.path.abspath(path)
        self.connections = connections
        self.docker_port = docker_port

    def name(self):
        return get_project_name(self.path)

    def record(self):
        config_file = os.path.join(self.path, "config.json")
        set_config_value("connections", [conn.__dict__ for conn in self.connections], config_file)
        set_config_value("docker_port", self.docker_port, config_file)

    @classmethod
    def extract(cls, path):
        local_config_file = os.path.join(path, "config.json")
        if not os.path.isfile(local_config_file):
            with open(local_config_file, "w") as config:
                json.dump({}, config, indent=4, sort_keys=True)

        with open(local_config_file, "r") as config:
            json_config = json.load(config)
            connections = [Connection.extract(connection) for connection in json_config.get("connections", [])]
            docker_port = json_config.get("docker_port", 8080)
            return Project(path, connections, docker_port)


def get_project_name(path):
    manifest_resources = os.path.join(path, "resources", "resources.properties")
    if os.path.isfile(manifest_resources):
        properties = load_properties(manifest_resources)
        return properties["DISPLAY_NAME"]
    else:
        return path


def get_project(arguments):
    # If a path is supplied, use it first
    path = arguments.path
    if ProjectValidator.is_project_dir(path):
        return _find_project_by_path(path)

    # Otherwise, check if the current directory is a project
    if ProjectValidator.is_project_dir(os.getcwd()):
        return _find_project_by_path(os.getcwd())

    # Finally, prompt the user for the project
    project_paths = get_config_value("projects", [])
    path = selection_prompt("Select a project: ",
                            [(path, get_project_name(path)) for path in project_paths if
                             ProjectValidator.is_project_dir(path)] + [("Other", "Other")])
    if path == "Other":
        path = path_prompt("Enter the path to the project: ", validator=ProjectValidator())

    return _find_project_by_path(path)


def record_project(project):
    _add_and_update_project_paths(project.path)
    project.record()
    return project


def read_project(path):
    return Project.extract(path)


def _find_project_by_path(path):
    path = os.path.abspath(path)
    _add_and_update_project_paths(path)
    return read_project(path)


def _add_and_update_project_paths(path):
    project_paths = set(get_config_value("projects", []))
    project_paths.add(path)
    set_config_value("projects",
                     sorted(list([path for path in project_paths if ProjectValidator.is_project_dir(path)])))
