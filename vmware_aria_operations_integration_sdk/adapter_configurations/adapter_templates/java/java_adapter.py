import json
import logging
import os
from importlib import resources
from io import TextIOWrapper
from string import Template
from typing import List
from typing import Union

from vmware_aria_operations_integration_sdk.adapter_configurations.adapter_config import (
    AdapterConfig,
)
from vmware_aria_operations_integration_sdk.adapter_configurations.adapter_config import (
    Question,
)
from vmware_aria_operations_integration_sdk.constant import VERSION_FILE
from vmware_aria_operations_integration_sdk.filesystem import mkdir
from vmware_aria_operations_integration_sdk.ui import prompt
from vmware_aria_operations_integration_sdk.ui import selection_prompt
from vmware_aria_operations_integration_sdk.validation.input_validators import (
    JavaPackageValidator,
)

logger = logging.getLogger(__name__)


class JavaAdapter(AdapterConfig):
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

        self.language = "java"
        self.source_code_directory_path = ""
        self.package_name = ""
        self.questions.append(
            Question(
                "package_name",
                prompt,
                message="Enter package name: ",
                default="com.mycompany",
                validator=JavaPackageValidator(),
                description="The package name will be used to setup the package used by the adapter and the directory "
                "structure of the project.",
            )
        )

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

    def get_file_destination(self, file: str) -> str:
        destination = super().get_file_destination(file)
        if "src" in file:
            destination = destination.replace(
                "src/main/java", self.source_code_directory_path
            )

        return destination

    def build_string_from_template(self, path: str) -> str:
        with open(path, "r") as template_file:
            output = template_file.read()
            template = Template(output)

        string_from_template = template.substitute({"package_name": self.package_name})

        return string_from_template

    def build_project_structure(self) -> None:
        self.package_name = self.response_values["package_name"]
        self.source_code_directory_path = os.path.join(
            "src", *self.package_name.split(".")
        )
        mkdir(self.project.path, self.source_code_directory_path)

    def build_commands_file(self) -> None:
        logger.debug("generating commands file")
        with open(os.path.join(self.project.path, "commands.cfg"), "w") as commands:
            command_and_executable = (
                f"/usr/bin/java -cp app.jar:dependencies/* {self.package_name}.Adapter"
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
            self._write_java_build_stage(dockerfile)
            self._write_java_execution_stage(dockerfile)

    def _write_java_build_stage(
        self,
        dockerfile: TextIOWrapper,
    ) -> None:
        # since the build stage should happen before the execution stage, we have to write it before
        dockerfile.seek(0)
        content = dockerfile.readlines()
        dockerfile.seek(0)

        dockerfile.write("# First Stage: Build the Java project using Gradle\n")
        dockerfile.write("FROM gradle:8.3.0-jdk17 AS build\n\n")
        dockerfile.write("# Set the working directory inside the Docker image\n")
        dockerfile.write("WORKDIR /home/gradle/project\n\n")
        dockerfile.write("# Copy the Gradle build file and the source code\n")
        dockerfile.write("COPY build.gradle .\n")
        dockerfile.write(f"COPY src src\n\n")
        dockerfile.write("# Run Gradle to compile the code\n")
        dockerfile.write("RUN gradle build\n\n")
        dockerfile.writelines(content)

    def _write_java_execution_stage(self, dockerfile: TextIOWrapper) -> None:
        dockerfile.write(f"WORKDIR /home/aria-ops-adapter-user/src/app\n\n")
        dockerfile.write(
            f"# Copy the compiled jar from the build stage and its dependencies\n"
        )
        dockerfile.write(
            f"COPY --from=build /home/gradle/project/build/libs/*.jar app.jar\n"
        )
        dockerfile.write(
            f"COPY --from=build /home/gradle/project/dependencies dependencies\n"
        )
