import json
import logging
from abc import ABC
from abc import abstractmethod
from importlib import resources
from shutil import copy
from typing import Any
from typing import Callable
from typing import Dict
from typing import Generator
from typing import List
from typing import TextIO
from typing import Union

from docker.tls import os
from git import Repo

from vmware_aria_operations_integration_sdk import adapter_configurations
from vmware_aria_operations_integration_sdk.constant import CONNECTIONS_FILE_NAME
from vmware_aria_operations_integration_sdk.constant import CONTAINER_BASE_NAME
from vmware_aria_operations_integration_sdk.constant import CONTAINER_REGISTRY_HOST
from vmware_aria_operations_integration_sdk.constant import CONTAINER_REGISTRY_PATH
from vmware_aria_operations_integration_sdk.constant import REPO_NAME
from vmware_aria_operations_integration_sdk.constant import VERSION_FILE
from vmware_aria_operations_integration_sdk.filesystem import mkdir
from vmware_aria_operations_integration_sdk.project import Project
from vmware_aria_operations_integration_sdk.project import record_project

logger = logging.getLogger(__name__)


class Question:
    def __init__(self, key: str, prompt: Callable, *args: Any, **kwargs: Any) -> None:
        self.key = key
        self.prompt = prompt
        self.prompt_args = args
        self.prompt_kwargs = kwargs

    def ask(self) -> Any:
        return self.prompt(*self.prompt_args, **self.prompt_kwargs)


class AdapterConfig(ABC):
    def __init__(
        self,
        project_path: str,
        display_name: str,
        adapter_key: str,
        adapter_description: str,
        vendor: str,
        eula_file_path: str,
        icon_file_path: str,
        questions: Union[None, List[Question]] = None,
    ) -> None:
        if questions is None:
            questions = []
        self.project = Project(project_path)
        self.display_name = display_name
        self.adapter_key = adapter_key
        self.adapter_description = adapter_description
        self.vendor = vendor
        self.eula_file_path = eula_file_path
        self.icon_file_path = icon_file_path
        self.questions = questions

        self.conf_dir_path = os.path.join(project_path, "conf")
        self.conf_resources_dir_path = os.path.join(project_path, "resources")
        self.conf_images_dir_path = os.path.join(project_path, "images")

        self.response_values: Dict[str, Any] = dict()

        self.language = ""
        self.templates = list()
        adapter_templates_dir_path = self.get_templates_directory()

        templates = [
            os.path.join(adapter_templates_dir_path, d)
            for d in os.listdir(adapter_templates_dir_path)
            if os.path.isdir(os.path.join(adapter_templates_dir_path, d))
            and not d.startswith(".")
            and not d.startswith("__")
        ]

        for template_directory_path in templates:
            template_display_name = " ".join(
                [
                    segment.capitalize()
                    for segment in os.path.basename(template_directory_path).split("_")
                ]
            )
            self.templates.append((template_directory_path, template_display_name))

    def prompt_config_values(self) -> None:
        """
        This function will prompt users for all the config values
        """
        for question in self.questions:
            self.response_values[question.key] = question.ask()

    @abstractmethod
    def build_string_from_template(self, path: str) -> str:
        """
        This function takes a path to a file template and returns the resulting file as a string
        """

    @abstractmethod
    def build_project_structure(
        self,
    ) -> None:
        """
        This method is called after generating the vanilla project structure
        this method should be used to generate any directory structure that is specific to
        the adapter
        """

    @abstractmethod
    def build_commands_file(self) -> None:
        """
        this file returns the contents of the commands.cfg
        """

    @abstractmethod
    def build_docker_file(self) -> None:
        """this method is reserved is for building the docker file"""

    @abstractmethod
    def get_templates_directory(self) -> str:
        pass

    def _build_content_directory(self) -> str:
        content_dir = mkdir(self.project.path, "content")
        self._add_git_keep_file(mkdir(content_dir, "policies"))
        self._add_git_keep_file(mkdir(content_dir, "traversalspecs"))
        self._add_git_keep_file(mkdir(content_dir, "resources"))
        self._add_git_keep_file(mkdir(content_dir, "customgroups"))
        self._add_git_keep_file(mkdir(content_dir, "reports"))
        self._add_git_keep_file(mkdir(content_dir, "recommendations"))
        self._add_git_keep_file(mkdir(content_dir, "dashboards"))

        files_dir = mkdir(content_dir, "files")
        self._add_git_keep_file(mkdir(files_dir, "topowidget"))
        self._add_git_keep_file(mkdir(files_dir, "txtwidget"))
        self._add_git_keep_file(mkdir(files_dir, "solutionconfig"))
        self._add_git_keep_file(mkdir(files_dir, "reskndmetric"))

        self._add_git_keep_file(mkdir(content_dir, "alertdefs"))
        self._add_git_keep_file(mkdir(content_dir, "supermetrics"))
        self._add_git_keep_file(mkdir(content_dir, "symptomdefs"))

        # These files are often created by the OS, and might cause errors if interacted with
        self.ignore_files = {".DS_Store", "Thumbs.db", "desktop.ini"}

        return content_dir

    def _add_git_keep_file(self, path: str) -> None:
        with open(os.path.join(path, ".gitkeep"), "w") as gitkeep:
            # Create empty .gitkeep file
            pass

    def _create_manifest_localization_file(self) -> None:
        mkdir(self.conf_resources_dir_path)
        resources_file = os.path.join(
            self.conf_resources_dir_path, "resources.properties"
        )
        with open(resources_file, "w") as resources_fd:
            resources_fd.write("#This is the default localization file.\n")
            resources_fd.write("\n")
            resources_fd.write("#The solution's localized name displayed in UI\n")
            resources_fd.write(f"DISPLAY_NAME={self.display_name}\n")
            resources_fd.write("\n")
            resources_fd.write("#The solution's localized description\n")
            resources_fd.write(f"DESCRIPTION={self.adapter_description}\n")
            resources_fd.write("\n")
            resources_fd.write("#The vendor's localized name\n")
            resources_fd.write(f"VENDOR={self.vendor}\n")

    def _create_eula_file(self) -> None:
        if not self.eula_file_path:
            self.eula_file_path = os.path.join(self.project.path, "eula.txt")
            with open(self.eula_file_path, "w") as eula_fd:
                # Note: VMware Aria Operations requires a EULA file, and it must not be blank.
                eula_fd.write("There is no EULA associated with this Management Pack.")
        else:
            copy(self.eula_file_path, self.project.path)

    def _create_icon_file(self) -> None:
        if not self.icon_file_path:
            self.icon_file_path = ""
        else:
            copy(self.icon_file_path, self.project.path)
            self.icon_file_path = os.path.basename(self.icon_file_path)

    def _create_manifest_file(self) -> None:
        self.manifest_file_path = os.path.join(self.project.path, "manifest.txt")
        manifest = {
            "display_name": "DISPLAY_NAME",
            "name": f"iSDK_{self.adapter_key}",
            "description": "DESCRIPTION",
            "version": "1.0.0",
            "vcops_minimum_version": "8.10.0",
            "disk_space_required": 500,
            "run_scripts_on_all_nodes": "true",
            "eula_file": self.eula_file_path,
            "platform": ["Linux Non-VA", "Linux VA"],
            "vendor": "VENDOR",
            "pak_icon": self.icon_file_path,
            "pak_validation_script": {"script": ""},
            "adapter_pre_script": {"script": ""},
            "adapter_post_script": {"script": ""},
            "adapters": ["adapter.zip"],
            "adapter_kinds": [self.adapter_key],
            "license_type": "",
        }
        with open(self.manifest_file_path, "w") as manifest_fd:
            json.dump(manifest, manifest_fd, indent=4)

    def _list_adapter_template_files(self) -> Generator:
        for root, dirs, files in os.walk(self.response_values["adapter_template_path"]):
            for _file in files:
                if _file in self.ignore_files:
                    continue

                full_path = os.path.join(root, _file)

                yield full_path

    def _build_integration_sdk_project_structure(self) -> None:
        mkdir(self.project.path)

        self._build_content_directory()

        mkdir(self.conf_dir_path)
        mkdir(self.conf_resources_dir_path)
        mkdir(self.conf_images_dir_path)

        self._add_git_keep_file(mkdir(self.conf_images_dir_path, "AdapterKind"))
        self._add_git_keep_file(mkdir(self.conf_images_dir_path, "ResourceKind"))
        self._add_git_keep_file(mkdir(self.conf_images_dir_path, "TraversalSpec"))

        self._create_manifest_localization_file()
        self._create_eula_file()
        self._create_icon_file()
        self._create_manifest_file()

        # This has to happen after the manifest.txt file is created, because this function only records a project if
        # it is an Integration SDK project. Currently, the method for determining this is to look for the manifest.txt
        # file. See `common/validation/input_validators.py`, class `ProjectValidator`
        record_project(self.project)

        # copy describe.xsd into conf directory
        with resources.path(adapter_configurations, "describeSchema.xsd") as src:
            copy(src, self.conf_dir_path)

        # copy alert definition specs xml schema into conf directory
        with resources.path(adapter_configurations, "alertDefinitionSchema.xsd") as src:
            dest = os.path.join(self.project.path, "content", "alertdefs")
            copy(src, dest)

        # copy traversal specs xml schema into conf directory
        with resources.path(adapter_configurations, "traversalSpecsSchema.xsd") as src:
            dest = os.path.join(self.project.path, "content", "traversalspecs")
            copy(src, dest)

    def create_project(self) -> None:
        """
        This method calls the different methods inside this class to build an adapter
        """
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            # Log directory must be writable by non-root users so that the adapter container
            # is able to create and write log files.
            log_dir = mkdir(self.project.path, "logs")
            os.chmod(log_dir, 0o755)

        self._build_integration_sdk_project_structure()

        self.build_project_structure()
        self.build_docker_file()
        self.build_commands_file()

        self._build_adapter_template()

        self._build_vcs_configuration()

    def write_base_execution_stage_image(
        self, dockerfile: TextIO, language: str
    ) -> None:

        with resources.path(
            "vmware_aria_operations_integration_sdk", VERSION_FILE
        ) as config_file:
            with open(config_file, "r") as config:
                config_json = json.load(config)
                images = [config_json["base_image"]] + config_json["secondary_images"]
        version = next(
            iter(
                filter(lambda image: image["language"].lower() == self.language, images)
            )
        )["version"]
        dockerfile.write(
            f"# If the harbor repo isn't accessible, the {CONTAINER_BASE_NAME} image can be built locally.\n"
        )
        dockerfile.write(
            f"# Go to the {REPO_NAME} repository, and run the build_images.py script located at "
            f"images/build_images.py\n"
        )
        dockerfile.write(
            f"FROM {CONTAINER_REGISTRY_HOST}/{CONTAINER_REGISTRY_PATH}/{CONTAINER_BASE_NAME}:{language}-{version}\n"
        )
        dockerfile.write(f"COPY commands.cfg .\n")

    def get_file_destination(self, file: str) -> str:
        return str(os.path.join(self.project.path, file))

    def _build_adapter_template(self) -> None:
        # Iterate through all files in the selected template
        for file in self._list_adapter_template_files():
            file_path, extension = os.path.splitext(
                file.replace(self.response_values["adapter_template_path"] + "/", "")
            )
            destination = self.get_file_destination(file_path)
            if extension == ".template":
                with open(destination, "w") as new_file:
                    new_file.write(self.build_string_from_template(file))
            else:
                destination = destination + extension
                copy(file, destination)

    def _build_vcs_configuration(self) -> None:
        # initialize new project as a git repository
        repo = Repo.init(self.project.path)
        git_ignore = os.path.join(self.project.path, ".gitignore")
        with open(git_ignore, "w") as git_ignore_fd:
            git_ignore_fd.write("logs\n")
            git_ignore_fd.write("build\n")
            git_ignore_fd.write(f"{CONNECTIONS_FILE_NAME}\n")
            git_ignore_fd.write(f"venv-{self.display_name}\n")
            git_ignore_fd.write("\n")

        repo.git.add(all=True)
        repo.index.commit("Initial commit.")

        # TODO: Prompt to create remote, once we know what the default remote should be.
        # remote = repo.create_remote("origin", url="https://gitlab.vmware.com/[...]")
        # remote.push(refspec='main:main')
