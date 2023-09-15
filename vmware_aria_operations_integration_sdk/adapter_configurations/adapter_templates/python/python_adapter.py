import json
import logging
import os
import venv
from importlib import resources
from io import TextIOWrapper
from string import Template

import pkg_resources

from vmware_aria_operations_integration_sdk.adapter_configurations.adapter_config import (
    AdapterConfig,
)
from vmware_aria_operations_integration_sdk.adapter_configurations.adapter_config import (
    Question,
)
from vmware_aria_operations_integration_sdk.constant import VERSION_FILE
from vmware_aria_operations_integration_sdk.filesystem import mkdir
from vmware_aria_operations_integration_sdk.ui import selection_prompt

logger = logging.getLogger(__name__)


class PythonAdapter(AdapterConfig):
    def __init__(
        self,
        project_path: str,
        display_name: str,
        adapter_key: str,
        adapter_description: str,
        vendor: str,
        eula_file_path: str,
        icon_file_path: str,
    ):
        super().__init__(
            project_path,
            display_name,
            adapter_key,
            adapter_description,
            vendor,
            eula_file_path,
            icon_file_path,
        )
        self.language = "python"
        self.source_code_directory_path = "app"

        items = list()
        adapter_templates_dir_path = os.path.dirname(os.path.realpath(__file__))
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
            items.append((template_directory_path, template_display_name))

        self.questions.append(
            Question(
                "adapter_template_path",
                selection_prompt,
                "Select a template for your project",
                items=items,
                description="- Sample Adapter: Generates a working adapter with comments "
                "throughout its code\n"
                "- New Adapter: The minimum necessary code to start developing "
                "an adapter\n\n"
                "For more information visit "
                "https://vmware.github.io/vmware-aria-operations-integration"
                "-sdk/get_started/#template-projects",
            )
        )

    def build_string_from_template(self, path: str) -> str:
        with open(path, "r") as template_file:
            template = Template(template_file.read())

        filename = os.path.basename(os.path.splitext(path)[0])

        string_from_template = ""
        if os.path.basename(path) == "constants.py.template":
            string_from_template = template.substitute(
                {"adapter_name": self.display_name, "adapter_kind": self.adapter_key}
            )

        return string_from_template

    def build_project_structure(self) -> None:
        mkdir(self.project.path, self.source_code_directory_path)

        # create development requirements file
        requirements_file = os.path.join(self.project.path, "requirements.txt")
        with open(requirements_file, "w") as requirements:
            package = "vmware-aria-operations-integration-sdk"
            version = pkg_resources.get_distribution(package).version
            requirements.write(f"{package}=={version}\n")

        env_dir = os.path.join(self.project.path, f"venv-{self.display_name}")
        venv.create(env_dir, with_pip=True)

        # # install requirements.txt into virtual environment
        # v_env = os.environ.copy()
        # v_env["VIRTUAL_ENV"] = env_dir
        # v_env["PATH"] = f"{env_dir}/bin:{v_env['PATH']}"
        # result = subprocess.run(
        #     ["pip", "install", "-r", f"{requirements_file}"],
        #     env=v_env,
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        # )
        # for line in result.stdout.decode("utf-8").splitlines():
        #     logger.debug(line)
        # for line in result.stderr.decode("utf-8").splitlines():
        #     logger.warning(line)
        # if result.returncode != 0:
        #     logger.error(
        #         "Could not install sdk tools into the development virtual environment."
        #     )

        namespace_package_indicator_file = os.path.join(
            self.project.path, self.source_code_directory_path, "__init__.py"
        )
        with open(namespace_package_indicator_file, "w"):
            os.utime(namespace_package_indicator_file)

    def build_commands_file(self) -> None:
        logger.debug("generating commands file")
        with open(os.path.join(self.project.path, "commands.cfg"), "w") as commands:
            command_and_executable = (
                f"/usr/local/bin/python {self.source_code_directory_path}/adapter.py"
            )

            commands.write("[Commands]\n")
            commands.write(f"test={command_and_executable} test\n")
            commands.write(f"collect={command_and_executable} collect\n")
            commands.write(
                f"adapter_definition={command_and_executable} adapter_definition\n"
            )
            commands.write(f"endpoint_urls={command_and_executable} endpoint_urls\n")

    def build_docker_file(self) -> None:
        logger.debug("generating Dockerfile")
        images = []
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

        with open(os.path.join(self.project.path, "Dockerfile"), "w+") as dockerfile:
            self.write_base_execution_stage_image(dockerfile, self.language, version)
            self._write_python_execution_stage(dockerfile)

    def add_gitignore_configuration(self, gitignore: TextIOWrapper) -> None:
        return

    def _write_python_execution_stage(self, dockerfile: TextIOWrapper) -> None:
        dockerfile.write(f"COPY adapter_requirements.txt .\n")
        dockerfile.write("RUN pip3 install -r adapter_requirements.txt --upgrade\n")

        # having the executable copied at the end allows the image to be built faster since previous
        # the previous intermediate image is cached
        dockerfile.write(
            f"COPY {self.source_code_directory_path} {self.source_code_directory_path}\n"
        )
