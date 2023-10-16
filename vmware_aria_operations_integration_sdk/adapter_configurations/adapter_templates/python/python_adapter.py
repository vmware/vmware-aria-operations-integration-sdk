import logging
import os
from typing import List
from typing import Optional
from typing import TextIO

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
        questions: Optional[List[Question]] = None,
    ):
        super().__init__(
            project_path,
            display_name,
            adapter_key,
            adapter_description,
            vendor,
            eula_file_path,
            icon_file_path,
            questions,
        )
        self.language = "python"
        self.source_code_directory_path = "app"

        self.questions.append(
            Question(
                "adapter_template_path",
                selection_prompt,
                "Select a template for your project:",
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
