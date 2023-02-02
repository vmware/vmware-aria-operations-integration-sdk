#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import json
import logging
import os
import subprocess
import traceback
import venv
from importlib import resources
from shutil import copy
from typing import Dict

import pkg_resources
from git import Repo

from vmware_aria_operations_integration_sdk import adapter_template
from vmware_aria_operations_integration_sdk.adapter_template import java
from vmware_aria_operations_integration_sdk.adapter_template import powershell
from vmware_aria_operations_integration_sdk.constant import CONTAINER_BASE_NAME
from vmware_aria_operations_integration_sdk.constant import CONTAINER_REGISTRY_HOST
from vmware_aria_operations_integration_sdk.constant import CONTAINER_REGISTRY_PATH
from vmware_aria_operations_integration_sdk.constant import REPO_NAME
from vmware_aria_operations_integration_sdk.constant import VERSION_FILE
from vmware_aria_operations_integration_sdk.filesystem import mkdir
from vmware_aria_operations_integration_sdk.filesystem import rmdir
from vmware_aria_operations_integration_sdk.logging_format import CustomFormatter
from vmware_aria_operations_integration_sdk.logging_format import PTKHandler
from vmware_aria_operations_integration_sdk.project import Project
from vmware_aria_operations_integration_sdk.project import record_project
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


def create_manifest_localization_file(
    path: str, name: str, vendor: str, description: str
) -> None:
    resources_dir = mkdir(path, "resources")
    resources_file = os.path.join(resources_dir, "resources.properties")
    with open(resources_file, "w") as resources_fd:
        resources_fd.write("#This is the default localization file.\n")
        resources_fd.write("\n")
        resources_fd.write("#The solution's localized name displayed in UI\n")
        resources_fd.write(f"DISPLAY_NAME={name}\n")
        resources_fd.write("\n")
        resources_fd.write("#The solution's localized description\n")
        resources_fd.write(f"DESCRIPTION={description}\n")
        resources_fd.write("\n")
        resources_fd.write("#The vendor's localized name\n")
        resources_fd.write(f"VENDOR={vendor}\n")


def create_eula_file(path: str, eula_file: str) -> str:
    if not eula_file:
        eula_file = "eula.txt"
        with open(os.path.join(path, eula_file), "w") as eula_fd:
            # Note: VMware Aria Operations requires a EULA file, and it must not be blank.
            eula_fd.write("There is no EULA associated with this Management Pack.")
    else:
        copy(eula_file, path)
        eula_file = os.path.basename(eula_file)

    return eula_file


def create_icon_file(path: str, icon_file: str) -> str:
    if not icon_file:
        icon_file = ""
    else:
        copy(icon_file, path)
        icon_file = os.path.basename(icon_file)

    return icon_file


def create_manifest_file(
    path: str, adapter_key: str, eula_file: str, icon_file: str
) -> Dict:
    manifest_file = os.path.join(path, "manifest.txt")
    manifest = {
        "display_name": "DISPLAY_NAME",
        "name": adapter_key,
        "description": "DESCRIPTION",
        "version": "1.0.0",
        "vcops_minimum_version": "8.10.0",
        "disk_space_required": 500,
        "run_scripts_on_all_nodes": "true",
        "eula_file": eula_file,
        "platform": ["Linux Non-VA", "Linux VA"],
        "vendor": "VENDOR",
        "pak_icon": icon_file,
        "pak_validation_script": {"script": ""},
        "adapter_pre_script": {"script": ""},
        "adapter_post_script": {"script": ""},
        "adapters": ["adapter.zip"],
        "adapter_kinds": [adapter_key],
        "license_type": "",
    }
    with open(manifest_file, "w") as manifest_fd:
        json.dump(manifest, manifest_fd, indent=4)

    return manifest


def build_content_directory(path: str) -> str:
    content_dir = mkdir(path, "content")
    add_git_keep_file(mkdir(content_dir, "policies"))
    add_git_keep_file(mkdir(content_dir, "traversalspecs"))
    add_git_keep_file(mkdir(content_dir, "resources"))
    add_git_keep_file(mkdir(content_dir, "customgroups"))
    add_git_keep_file(mkdir(content_dir, "reports"))
    add_git_keep_file(mkdir(content_dir, "recommendations"))
    add_git_keep_file(mkdir(content_dir, "dashboards"))

    files_dir = mkdir(content_dir, "files")
    add_git_keep_file(mkdir(files_dir, "topowidget"))
    add_git_keep_file(mkdir(files_dir, "txtwidget"))
    add_git_keep_file(mkdir(files_dir, "solutionconfig"))
    add_git_keep_file(mkdir(files_dir, "reskndmetric"))

    add_git_keep_file(mkdir(content_dir, "alertdefs"))
    add_git_keep_file(mkdir(content_dir, "supermetrics"))
    add_git_keep_file(mkdir(content_dir, "symptomdefs"))

    return content_dir


def add_git_keep_file(path: str) -> None:
    with open(os.path.join(path, ".gitkeep"), "w") as gitkeep:
        # Create empty .gitkeep file
        pass


def create_project(
    path: str,
    name: str,
    adapter_key: str,
    description: str,
    vendor: str,
    eula_file: str,
    icon_file: str,
    language: str,
) -> None:
    mkdir(path)

    project = Project(path)

    build_content_directory(path)
    conf_dir = mkdir(path, "conf")
    conf_resources_dir = mkdir(path, "conf", "resources")

    create_manifest_localization_file(path, name, vendor, description)
    eula_file = create_eula_file(path, eula_file)
    icon_file = create_icon_file(path, icon_file)
    manifest = create_manifest_file(path, adapter_key, eula_file, icon_file)

    # This has to happen after the manifest.txt file is created, because this function only records a project if
    # it is an Integration SDK project. Currently, the method for determining this is to look for the manifest.txt
    # file. See `common/validation/input_validators.py`, class `ProjectValidator`
    record_project(project)

    # copy describe.xsd into conf directory
    with resources.path(adapter_template, "describeSchema.xsd") as src:
        dest = os.path.join(path, "conf")
        copy(src, dest)

    # copy alert definition specs xml schema into conf directory
    with resources.path(adapter_template, "alertDefinitionSchema.xsd") as src:
        dest = os.path.join(path, "content", "alertdefs")
        copy(src, dest)

    # copy traversal specs xml schema into conf directory
    with resources.path(adapter_template, "traversalSpecsSchema.xsd") as src:
        dest = os.path.join(path, "content", "traversalspecs")
        copy(src, dest)

    # create project structure
    executable_directory_path = build_project_structure(
        path, adapter_key, name, language
    )

    # create Dockerfile
    create_dockerfile(language, path, executable_directory_path)

    # create Commands File
    create_commands_file(language, path, executable_directory_path)

    # initialize new project as a git repository
    repo = Repo.init(path)
    git_ignore = os.path.join(path, ".gitignore")
    with open(git_ignore, "w") as git_ignore_fd:
        git_ignore_fd.write("logs\n")
        git_ignore_fd.write("build\n")
        git_ignore_fd.write("config.json\n")
        git_ignore_fd.write(f"venv-{name}\n")
        git_ignore_fd.write("\n")
    repo.git.add(all=True)
    repo.index.commit("Initial commit.")
    # TODO: Prompt to create remote, once we know what the default remote should be.
    # remote = repo.create_remote("origin", url="https://gitlab.vmware.com/[...]")
    # remote.push(refspec='main:main')


def main() -> None:
    path = ""
    try:
        path = path_prompt(
            "Enter a directory to create the project in. This is the directory where adapter code, metadata, and \n"
            "content will reside. If the directory doesn't already exist, it will be created. \nPath: ",
            validator=NewProjectDirectoryValidator(),
        )

        name = prompt(
            "Management pack display name: ",
            validator=NotEmptyValidator("Display name"),
            description="VMware Aria Operations uses the display name as the name of the Management \n"
            "Pack generated by this project. The name should include the name of the technology\n"
            "the Management Pack monitors.",
        )
        adapter_key = prompt(
            "Management pack adapter key: ",
            validator=AdapterKeyValidator(),
            default=AdapterKeyValidator.default(name),
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

        language = selection_prompt(
            "Select a language for the adapter.",
            items=[
                ("python", "Python"),
                ("java", "Java", "Unavailable for beta release"),
                ("powershell", "PowerShell", "Unavailable for beta release"),
            ],
            description="The language for the Management Pack determines the language for the template\n"
            "source and build files.",
        )
        # create project_directory
        with Spinner("Creating Project"):
            create_project(
                path,
                name,
                adapter_key,
                description,
                vendor,
                eula_file,
                icon_file,
                language,
            )
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


def create_dockerfile(
    language: str, root_directory: str, executable_directory_path: str
) -> None:
    logger.debug("generating Dockerfile")
    images = []
    with resources.path(__package__, VERSION_FILE) as config_file:
        with open(config_file, "r") as config:
            config_json = json.load(config)
            images = [config_json["base_image"]] + config_json["secondary_images"]
    version = next(
        iter(filter(lambda image: image["language"].lower() == language, images))
    )["version"]

    with open(os.path.join(root_directory, "Dockerfile"), "w") as dockerfile:
        # NOTE: This host is only accessible internally, for future releases we have to provide a public host
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

        if "python" in language:
            dockerfile.write(f"COPY adapter_requirements.txt .\n")
            dockerfile.write("RUN pip3 install -r adapter_requirements.txt --upgrade\n")

        # having the executable copied at the end allows the image to be built faster since previous
        # the previous intermediate image is cached
        dockerfile.write(
            f"COPY {executable_directory_path} {executable_directory_path}\n"
        )


def create_commands_file(
    language: str, path: str, executable_directory_path: str
) -> None:
    logger.debug("generating commands file")
    with open(os.path.join(path, "commands.cfg"), "w") as commands:
        command_and_executable = ""
        if "java" == language:
            command_and_executable = (
                f"/usr/bin/java -cp {executable_directory_path} Collector"
            )
        elif "python" == language:
            command_and_executable = (
                f"/usr/local/bin/python {executable_directory_path}/adapter.py"
            )
        elif "powershell" == language:
            command_and_executable = (
                f"/usr/bin/pwsh {executable_directory_path}/collector.ps1"
            )
        else:
            logger.error(f"language {language} is not supported")
            exit(1)

        commands.write("[Commands]\n")
        commands.write(f"test={command_and_executable} test\n")
        commands.write(f"collect={command_and_executable} collect\n")
        commands.write(
            f"adapter_definition={command_and_executable} adapter_definition\n"
        )
        commands.write(f"endpoint_urls={command_and_executable} endpoint_urls\n")


def build_project_structure(
    path: str, adapter_kind: str, name: str, language: str
) -> str:
    logger.debug("generating project structure")
    project_directory = ""  # this is where all the source code will reside

    if language == "python":
        project_directory = "app"
        mkdir(path, project_directory)

        # create template requirements.txt
        requirements_file = os.path.join(path, "adapter_requirements.txt")
        with open(requirements_file, "w") as requirements:
            requirements.write("psutil==5.9.0\n")
            requirements.write("vmware-aria-operations-integration-sdk-lib==0.5.*\n")

        # create development requirements file
        requirements_file = os.path.join(path, "requirements.txt")
        with open(requirements_file, "w") as requirements:
            package = "vmware-aria-operations-integration-sdk"
            version = pkg_resources.get_distribution(package).version
            requirements.write(f"{package}=={version}\n")

        env_dir = os.path.join(path, f"venv-{name}")
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

        # copy adapter.py into app directory
        with resources.path(adapter_template, "adapter.py") as src:
            dest = os.path.join(path, project_directory)
            copy(src, dest)

        with open(
            os.path.join(path, project_directory, "constants.py"), "w"
        ) as constants:
            constants.write(f'ADAPTER_KIND = "{adapter_kind}"\n')
            constants.write(f'ADAPTER_NAME = "{name}"\n')

    if language == "java":
        # TODO: copy a java class instead of generate it

        mkdir(path, "src")
        java.build_template(path, "src")

        project_directory = "out"
        mkdir(path, project_directory)
        java.compile(
            os.path.join(path, ""),
            os.path.join(
                path,
                project_directory,
            ),
        )

    if language == "powershell":
        # TODO: copy a powershell script  instead of generate it

        project_directory = "scripts"
        mkdir(path, project_directory)
        powershell.build_template(path, project_directory)

    return project_directory


if __name__ == "__main__":
    main()
