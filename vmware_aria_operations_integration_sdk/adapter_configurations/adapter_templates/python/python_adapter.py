import logging
import os
import subprocess
import venv
from string import Template
from typing import TextIO

import pkg_resources

from vmware_aria_operations_integration_sdk.adapter_configurations.adapter_config import (
    AdapterConfig,
)
from vmware_aria_operations_integration_sdk.adapter_configurations.adapter_config import (
    Question,
)
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

        self.questions.append(
            Question(
                "adapter_template_path",
                selection_prompt,
                "Select a template for your project",
                items=self.templates,
                description="- Sample Adapter: Generates a working adapter with comments "
                "throughout its code\n"
                "- New Adapter: The minimum necessary code to start developing "
                "an adapter\n\n"
                "For more information visit "
                "https://vmware.github.io/vmware-aria-operations-integration"
                "-sdk/get_started/#template-projects",
            )
        )

    def get_templates_directory(self) -> str:
        return os.path.dirname(os.path.realpath(__file__))

    def build_project_structure(self) -> None:
        mkdir(self.project.path, self.source_code_directory_path)
        namespace_package_indicator_file = os.path.join(
            self.project.path, self.source_code_directory_path, "__init__.py"
        )
        with open(namespace_package_indicator_file, "w"):
            os.utime(namespace_package_indicator_file)

        requirements_file = self.build_requirements_file()
        self.build_virtual_environment_and_install_requirements(requirements_file)

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

        with open(os.path.join(self.project.path, "Dockerfile"), "w+") as dockerfile:
            self.write_base_execution_stage_image(dockerfile, self.language)
            self._write_python_execution_stage(dockerfile)

    def _write_python_execution_stage(self, dockerfile: TextIO) -> None:
        dockerfile.write(f"COPY adapter_requirements.txt .\n")
        dockerfile.write("RUN pip3 install -r adapter_requirements.txt --upgrade\n")

        # having the executable copied at the end allows the image to be built faster since previous
        # the previous intermediate image is cached
        dockerfile.write(f"COPY app app\n")

    def build_requirements_file(self) -> str:
        requirements_file = os.path.join(self.project.path, "requirements.txt")
        with open(requirements_file, "w") as requirements:
            package = "vmware-aria-operations-integration-sdk"
            version = pkg_resources.get_distribution(package).version
            requirements.write(f"{package}=={version}\n")
        return requirements_file

    def build_virtual_environment_and_install_requirements(
        self, requirements_file: str
    ) -> None:
        env_dir = os.path.join(self.project.path, f"venv-{self.display_name}")
        venv.create(env_dir, with_pip=True)

        # install requirements.txt into virtual environment
        v_env = os.environ.copy()
        v_env["VIRTUAL_ENV"] = env_dir
        v_env["PATH"] = f"{env_dir}/bin:{v_env['PATH']}"
        result = subprocess.run(
            ["pip", "install", "-r", f"{requirements_file}"],
            env=v_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for line in result.stdout.decode("utf-8").splitlines():
            logger.debug(line)
        for line in result.stderr.decode("utf-8").splitlines():
            logger.warning(line)
        if result.returncode != 0:
            logger.error(
                "Could not install sdk tools into the development virtual environment."
            )
