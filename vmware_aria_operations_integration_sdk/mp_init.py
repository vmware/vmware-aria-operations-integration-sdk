#  Copyright 2022-2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import argparse
import logging
import os
import traceback

import pkg_resources

from vmware_aria_operations_integration_sdk.adapter_configurations.adapter_config import (
    AdapterConfig,
)
from vmware_aria_operations_integration_sdk.adapter_configurations.adapter_templates.java.java_adapter import (
    JavaAdapter,
)
from vmware_aria_operations_integration_sdk.adapter_configurations.adapter_templates.python.python_adapter import (
    PythonAdapter,
)
from vmware_aria_operations_integration_sdk.filesystem import rmdir
from vmware_aria_operations_integration_sdk.logging_format import CustomFormatter
from vmware_aria_operations_integration_sdk.logging_format import PTKHandler
from vmware_aria_operations_integration_sdk.ui import path_prompt
from vmware_aria_operations_integration_sdk.ui import print_formatted as print
from vmware_aria_operations_integration_sdk.ui import prompt
from vmware_aria_operations_integration_sdk.ui import selection_prompt
from vmware_aria_operations_integration_sdk.ui import Spinner
from vmware_aria_operations_integration_sdk.validation.input_validators import (
    AdapterKeyValidator,
)
from vmware_aria_operations_integration_sdk.validation.input_validators import (
    EulaValidator,
)
from vmware_aria_operations_integration_sdk.validation.input_validators import (
    ImageValidator,
)
from vmware_aria_operations_integration_sdk.validation.input_validators import (
    NewProjectDirectoryValidator,
)
from vmware_aria_operations_integration_sdk.validation.input_validators import (
    NotEmptyValidator,
)

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = PTKHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)


def main() -> None:
    description = "Tool for creating a new Management Pack for VMware Aria Operations."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=pkg_resources.get_distribution(
            "vmware-aria-operations-integration-sdk"
        ).version,
    )
    parser.parse_args()

    if hasattr(os, "geteuid") and os.geteuid() == 0:
        if (
            selection_prompt(
                "Detected that 'mp-init' is being run as root or using sudo. This is not "
                "recommended. Continue?",
                [("no", "No"), ("yes", "Yes")],
                "If 'mp-init' proceeds as root:\n"
                " * Some directories will need write permissions by non-root users.\n"
                " * Elevated permissions will also be required when running 'mp-test' and 'mp-build'\n"
                " * There may be other unexpected behavior",
            )
            == "no"
        ):
            exit(0)
    path = ""
    try:
        path = path_prompt(
            "Enter a directory to create the project in. This is the directory where adapter code, metadata, and \n"
            "content will reside. If the directory doesn't already exist, it will be created. \nPath: ",
            validator=NewProjectDirectoryValidator(),
        )

        display_name = prompt(
            "Management pack display name: ",
            validator=NotEmptyValidator("Display name"),
            description="VMware Aria Operations uses the display name as the name of the Management \n"
            "Pack generated by this project. The name should include the name of the technology\n"
            "the Management Pack monitors.",
        )
        adapter_key = prompt(
            "Management pack adapter key: ",
            validator=AdapterKeyValidator(),
            default=AdapterKeyValidator.default(display_name),
            description="The adapter key is used internally to identify the Management Pack and Adapter. It\n"
            "should be unique and cannot contain spaces or other special characters. It also \n"
            "cannot start with a number. By default, it is set to the Display Name with special\n"
            "characters removed (if the Display Name begins with a number, 'Adapter' is prepended).",
        )
        description = prompt(
            "Management pack description: ",
            validator=NotEmptyValidator("Description"),
            description="A brief description of the Management Pack and the technology it monitors. The \n"
            "description should include relevant versions of the monitored technology. ",
        )
        vendor = prompt(
            "Management pack vendor: ",
            validator=NotEmptyValidator("Vendor"),
            description="The name of the vendor/developer of the Management Pack. VMware Aria Operations\n"
            "will display this information during the installation of the  Management\n"
            "Pack generated by this project.",
        )
        eula_file = path_prompt(
            "Enter a path to a EULA text file, or leave blank for no EULA: ",
            validator=EulaValidator(),
            description="The End-User License Agreement (EULA) is a text file that provides guidelines for \n"
            "distributing and using the Management Pack generated by this project. It is generally\n"
            "only necessary for Management Packs that will be distributed. The content of this \n"
            "file appears in VMware Aria Operations during the installation of this \n"
            "management pack.",
        )

        if eula_file == "":
            print(
                "A EULA can be added later by editing the default 'eula.txt' file.",
                "class:information",
            )
        icon_file = path_prompt(
            "Enter a path to the management pack icon file, or leave blank for no icon: ",
            validator=ImageValidator(),
            description="The icon for the Management Pack generated by this project. The icon\n"
            "will be displayed in VMware Aria Operations. The icon image must be\n"
            "256x256 pixels in PNG format.",
        )
        if icon_file == "":
            print(
                "An icon can be added later by setting the 'pak_icon' key in 'manifest.txt' to the \n"
                "icon file name and adding the icon file to the root project directory.",
                "class:information",
            )

        adapter_config: AdapterConfig = selection_prompt(
            "Select a language for the adapter:",
            items=[
                (
                    PythonAdapter(
                        project_path=path,
                        display_name=display_name,
                        adapter_key=adapter_key,
                        adapter_description=description,
                        vendor=vendor,
                        eula_file_path=eula_file,
                        icon_file_path=icon_file,
                    ),
                    "Python",
                ),
                (
                    JavaAdapter(
                        project_path=path,
                        display_name=display_name,
                        adapter_key=adapter_key,
                        adapter_description=description,
                        vendor=vendor,
                        eula_file_path=eula_file,
                        icon_file_path=icon_file,
                    ),
                    "Java",
                ),
            ],
            description="The language for the Management Pack determines the language for the template\n"
            "source and build files.",
        )

        adapter_config.prompt_config_values()

        with Spinner("Creating Project"):
            adapter_config.create_project()

        with Spinner("Creating Virtual Environment"):
            adapter_config.create_virtual_environment()

        print("")
        print("")
        print("project generation completed", "class:success")
    except (KeyboardInterrupt, Exception, SystemExit) as error:
        # In all cases, we want to clean up afterwards
        if os.path.exists(path):
            logger.debug("Deleting generated artifacts")
            rmdir(path)

        if type(error) is KeyboardInterrupt:
            logger.info("Init cancelled by user")
        elif type(error) is SystemExit:
            exit(error.code)
        else:
            print("Unexpected error")
            logger.error(error)
            traceback.print_tb(error.__traceback__)


if __name__ == "__main__":
    main()
