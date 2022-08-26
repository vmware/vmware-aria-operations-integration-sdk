#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import json
import os
from typing import Optional

from vrealize_operations_integration_sdk.config import get_config_value, set_config_value
from vrealize_operations_integration_sdk.propertiesfile import load_properties
from vrealize_operations_integration_sdk.ui import selection_prompt, path_prompt
from vrealize_operations_integration_sdk.validation.input_validators import ProjectValidator


class Connection:
    def __init__(self, name: str,
                 identifiers: dict[str, any],
                 credential: dict[str, any],
                 certificates: Optional[list[str]] = None):
        self.name = name
        self.identifiers = identifiers
        self.credential = credential
        self.certificates = certificates

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
    set_config_value("projects", list([path for path in project_paths if ProjectValidator.is_project_dir(path)]))
