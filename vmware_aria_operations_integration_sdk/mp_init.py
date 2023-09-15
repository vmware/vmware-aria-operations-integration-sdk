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


# def create_manifest_localization_file(
#     path: str, name: str, vendor: str, description: str
# ) -> None:
#     resources_dir = mkdir(path, "resources")
#     resources_file = os.path.join(resources_dir, "resources.properties")
#     with open(resources_file, "w") as resources_fd:
#         resources_fd.write("#This is the default localization file.\n")
#         resources_fd.write("\n")
#         resources_fd.write("#The solution's localized name displayed in UI\n")
#         resources_fd.write(f"DISPLAY_NAME={name}\n")
#         resources_fd.write("\n")
#         resources_fd.write("#The solution's localized description\n")
#         resources_fd.write(f"DESCRIPTION={description}\n")
#         resources_fd.write("\n")
#         resources_fd.write("#The vendor's localized name\n")
#         resources_fd.write(f"VENDOR={vendor}\n")
#
#
# def create_eula_file(path: str, eula_file: str) -> str:
#     if not eula_file:
#         eula_file = "eula.txt"
#         with open(os.path.join(path, eula_file), "w") as eula_fd:
#             # Note: VMware Aria Operations requires a EULA file, and it must not be blank.
#             eula_fd.write("There is no EULA associated with this Management Pack.")
#     else:
#         copy(eula_file, path)
#         eula_file = os.path.basename(eula_file)
#
#     return eula_file
#
#
# def create_icon_file(path: str, icon_file: str) -> str:
#     if not icon_file:
#         icon_file = ""
#     else:
#         copy(icon_file, path)
#         icon_file = os.path.basename(icon_file)
#
#     return icon_file
#
#
# def create_manifest_file(
#     path: str, adapter_key: str, eula_file: str, icon_file: str
# ) -> Dict:
#     manifest_file = os.path.join(path, "manifest.txt")
#     manifest = {
#         "display_name": "DISPLAY_NAME",
#         "name": f"iSDK_{adapter_key}",
#         "description": "DESCRIPTION",
#         "version": "1.0.0",
#         "vcops_minimum_version": "8.10.0",
#         "disk_space_required": 500,
#         "run_scripts_on_all_nodes": "true",
#         "eula_file": eula_file,
#         "platform": ["Linux Non-VA", "Linux VA"],
#         "vendor": "VENDOR",
#         "pak_icon": icon_file,
#         "pak_validation_script": {"script": ""},
#         "adapter_pre_script": {"script": ""},
#         "adapter_post_script": {"script": ""},
#         "adapters": ["adapter.zip"],
#         "adapter_kinds": [adapter_key],
#         "license_type": "",
#     }
#     with open(manifest_file, "w") as manifest_fd:
#         json.dump(manifest, manifest_fd, indent=4)
#
#     return manifest


# def build_content_directory(path: str) -> str:
#     content_dir = mkdir(path, "content")
#     add_git_keep_file(mkdir(content_dir, "policies"))
#     add_git_keep_file(mkdir(content_dir, "traversalspecs"))
#     add_git_keep_file(mkdir(content_dir, "resources"))
#     add_git_keep_file(mkdir(content_dir, "customgroups"))
#     add_git_keep_file(mkdir(content_dir, "reports"))
#     add_git_keep_file(mkdir(content_dir, "recommendations"))
#     add_git_keep_file(mkdir(content_dir, "dashboards"))
#
#     files_dir = mkdir(content_dir, "files")
#     add_git_keep_file(mkdir(files_dir, "topowidget"))
#     add_git_keep_file(mkdir(files_dir, "txtwidget"))
#     add_git_keep_file(mkdir(files_dir, "solutionconfig"))
#     add_git_keep_file(mkdir(files_dir, "reskndmetric"))
#
#     add_git_keep_file(mkdir(content_dir, "alertdefs"))
#     add_git_keep_file(mkdir(content_dir, "supermetrics"))
#     add_git_keep_file(mkdir(content_dir, "symptomdefs"))
#
#     return content_dir

# def create_project(
#     path: str,
#     name: str,
#     adapter_key: str,
#     description: str,
#     vendor: str,
#     eula_file: str,
#     icon_file: str,
#     adapter_config: AdapterConfig,
#     template_style: str,
# ) -> None:
#     mkdir(path)
#
#     project = Project(path)
#
#     build_content_directory(path)
#     conf_dir = mkdir(path, "conf")
#     conf_resources_dir = mkdir(conf_dir, "resources")
#     conf_images_dir = mkdir(conf_dir, "images")
#     add_git_keep_file(mkdir(conf_images_dir, "AdapterKind"))
#     add_git_keep_file(mkdir(conf_images_dir, "ResourceKind"))
#     add_git_keep_file(mkdir(conf_images_dir, "TraversalSpec"))
#
#     create_manifest_localization_file(path, name, vendor, description)
#     eula_file = create_eula_file(path, eula_file)
#     icon_file = create_icon_file(path, icon_file)
#     manifest = create_manifest_file(path, adapter_key, eula_file, icon_file)
#
#     # This has to happen after the manifest.txt file is created, because this function only records a project if
#     # it is an Integration SDK project. Currently, the method for determining this is to look for the manifest.txt
#     # file. See `common/validation/input_validators.py`, class `ProjectValidator`
#     record_project(project)
#
#     # copy describe.xsd into conf directory
#     with resources.path(adapter_template, "describeSchema.xsd") as src:
#         dest = os.path.join(path, "conf")
#         copy(src, dest)
#
#     # copy alert definition specs xml schema into conf directory
#     with resources.path(adapter_template, "alertDefinitionSchema.xsd") as src:
#         dest = os.path.join(path, "content", "alertdefs")
#         copy(src, dest)
#
#     # copy traversal specs xml schema into conf directory
#     with resources.path(adapter_template, "traversalSpecsSchema.xsd") as src:
#         dest = os.path.join(path, "content", "traversalspecs")
#         copy(src, dest)
#
#     # create project structure
#     source_code_directory_path = build_project_structure(
#         path, adapter_key, name, adapter_config, template_style
#     )
#
#     # create Dockerfile
#     create_dockerfile(adapter_config.language, path, source_code_directory_path)
#
#     # create Commands File
#     create_commands_file(adapter_config.language, path, source_code_directory_path)
#
#     # initialize new project as a git repository
#     repo = Repo.init(path)
#     git_ignore = os.path.join(path, ".gitignore")
#     with open(git_ignore, "w") as git_ignore_fd:
#         git_ignore_fd.write("logs\n")
#         git_ignore_fd.write("build\n")
#         git_ignore_fd.write(f"{CONNECTIONS_FILE_NAME}\n")
#         git_ignore_fd.write(f"venv-{name}\n")
#         git_ignore_fd.write("\n")
#     repo.git.add(all=True)
#     repo.index.commit("Initial commit.")
#     # TODO: Prompt to create remote, once we know what the default remote should be.
#     # remote = repo.create_remote("origin", url="https://gitlab.vmware.com/[...]")
#     # remote.push(refspec='main:main')


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
            "Select a language for the adapter.",
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

        # create project_directory
        with Spinner("Creating Project"):
            adapter_config.create_project()
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
