#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import json
import os

from common.config import get_config_value, set_config_value
from common.propertiesfile import load_properties
from common.ui import selection_prompt, path_prompt
from common.validation.input_validators import ProjectValidator


class Connection:
    def __init__(self, name: str, identifiers: dict[str, any], credential: dict[str, any]):
        self.name = name
        self.identifiers = identifiers
        self.credential = credential

    @classmethod
    def extract(cls, json):
        name = json["name"]
        identifiers = json["identifiers"]
        credential = json["credential"]
        return Connection(name, identifiers, credential)


class Project:
    def __init__(self, path: str, connections: list[Connection] = None, docker_port: int = 8080):
        if connections is None:
            connections = []
        self.path = os.path.abspath(path)
        self.connections = connections
        self.docker_port = docker_port

    def name(self):
        return get_project_name(self.path)

    def record(self, config_file):
        set_config_value("path", self.path, config_file)
        set_config_value("connections", [conn.__dict__ for conn in self.connections], config_file)
        set_config_value("docker_port", self.docker_port, config_file)

    @classmethod
    def extract(cls, json):
        path = json["path"]
        connections = [Connection.extract(connection) for connection in json.get("connections", [])]
        docker_port = json.get("docker_port", 8080)
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

    local_config_file = os.path.join(project.path, "config.json")
    project.record(local_config_file)
    return project


def read_project(path):
    local_config_file = os.path.join(path, "config.json")
    if not os.path.isfile(local_config_file):
        with open(local_config_file, "w") as config:
            json.dump({"path": path}, config, indent=4, sort_keys=True)

    with open(local_config_file, "r") as config:
        return Project.extract(json.load(config))


def _find_project_by_path(path):
    path = os.path.abspath(path)
    _add_and_update_project_paths(path)
    return read_project(path)


def _add_and_update_project_paths(path):
    project_paths = set(get_config_value("projects", []))
    project_paths.add(path)
    set_config_value("projects", list([path for path in project_paths if ProjectValidator.is_project_dir(path)]))
