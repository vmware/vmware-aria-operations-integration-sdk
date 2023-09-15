from io import TextIOWrapper

from vmware_aria_operations_integration_sdk.adapter_configurations.adapter_config import (
    AdapterConfig,
)


class JavaAdapter(AdapterConfig):
    def build_string_from_template(self, path: str) -> str:
        pass

    def build_project_structure(self) -> None:
        pass

    def build_commands_file(self) -> None:
        pass

    def build_docker_file(self) -> None:
        pass

    def add_gitignore_configuration(self, gitignore: TextIOWrapper) -> None:
        pass
