import os

from common.config import get_config_value, set_config_value
from common.ui import selection_prompt, path_prompt
from common.validation.input_validators import ProjectValidator


class Connection:
    # TODO: Make better use of the Project and Connection classes, or remove them
    def __init__(self, name: str, identifiers: dict[str, any], credential: dict[str, any]):
        self.name = name
        self.identifiers = identifiers
        self.credential = credential


class Project:
    # TODO: Make better use of the Project and Connection classes, or remove them
    def __init__(self, path: str, connections: list[Connection] = None, docker_port: int = 8080):
        if connections is None:
            connections = []
        self.path = os.path.abspath(path)
        self.connections = connections
        self.docker_port = docker_port


def get_project(arguments):
    # If a path is supplied, use it first
    path = arguments.path
    if ProjectValidator.is_project_dir(path):
        return find_project_by_path(path)

    # Otherwise, check if the current directory is a project
    if ProjectValidator.is_project_dir(os.getcwd()):
        return find_project_by_path(os.getcwd())

    # Finally, prompt the user for the project
    projects = get_config_value("projects", [])
    path = selection_prompt("Select a project: ", [(project["path"], project["path"]) for project in projects] + [("Other", "Other")])
    if path == "Other":
        path = path_prompt("Enter the path to the project: ", validator=ProjectValidator())

    return find_project_by_path(path)


def record_project(project):
    existing_projects = get_config_value("projects", [])
    projects_by_path = {existing_project["path"]: existing_project for existing_project in existing_projects}
    projects_by_path[project["path"]] = project
    set_config_value("projects", list(projects_by_path.values()))
    return project


def find_project_by_path(path):
    projects = get_config_value("projects", [])
    for existing_project in projects:
        if existing_project["path"] == os.path.abspath(path):
            return existing_project
    project = Project(path).__dict__
    projects.append(project)
    set_config_value("projects", projects)
    return project
