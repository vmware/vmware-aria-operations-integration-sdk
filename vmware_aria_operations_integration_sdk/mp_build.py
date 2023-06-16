#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import argparse
import asyncio
import collections
import json
import logging
import os
import re
import shutil
import time
import traceback
import zipfile
from logging.handlers import RotatingFileHandler
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

import httpx
import pkg_resources
from docker import DockerClient
from docker.models.images import Image

from vmware_aria_operations_integration_sdk import ui
from vmware_aria_operations_integration_sdk.adapter_container import AdapterContainer
from vmware_aria_operations_integration_sdk.config import get_config_value
from vmware_aria_operations_integration_sdk.config import set_config_value
from vmware_aria_operations_integration_sdk.constant import API_VERSION_ENDPOINT
from vmware_aria_operations_integration_sdk.constant import (
    CONFIG_CONTAINER_REGISTRY_KEY,
)
from vmware_aria_operations_integration_sdk.constant import (
    CONFIG_DEFAULT_CONTAINER_REGISTRY_PATH_KEY,
)
from vmware_aria_operations_integration_sdk.constant import (
    CONFIG_DEFAULT_MEMORY_LIMIT_KEY,
)
from vmware_aria_operations_integration_sdk.constant import (
    CONFIG_FALLBACK_CONTAINER_REGISTRY_KEY,
)
from vmware_aria_operations_integration_sdk.containerized_adapter_rest_api import (
    send_get_to_adapter,
)
from vmware_aria_operations_integration_sdk.describe import Describe
from vmware_aria_operations_integration_sdk.describe import get_adapter_kind
from vmware_aria_operations_integration_sdk.describe import write_describe
from vmware_aria_operations_integration_sdk.docker_wrapper import build_image
from vmware_aria_operations_integration_sdk.docker_wrapper import DockerWrapperError
from vmware_aria_operations_integration_sdk.docker_wrapper import init
from vmware_aria_operations_integration_sdk.docker_wrapper import login
from vmware_aria_operations_integration_sdk.docker_wrapper import LoginError
from vmware_aria_operations_integration_sdk.docker_wrapper import push_image
from vmware_aria_operations_integration_sdk.docker_wrapper import PushError
from vmware_aria_operations_integration_sdk.filesystem import mkdir
from vmware_aria_operations_integration_sdk.filesystem import rm
from vmware_aria_operations_integration_sdk.filesystem import rmdir
from vmware_aria_operations_integration_sdk.filesystem import zip_dir
from vmware_aria_operations_integration_sdk.filesystem import zip_file
from vmware_aria_operations_integration_sdk.logging_format import CustomFormatter
from vmware_aria_operations_integration_sdk.logging_format import PTKHandler
from vmware_aria_operations_integration_sdk.project import get_project
from vmware_aria_operations_integration_sdk.propertiesfile import write_properties
from vmware_aria_operations_integration_sdk.ui import print_formatted as print
from vmware_aria_operations_integration_sdk.ui import prompt
from vmware_aria_operations_integration_sdk.ui import selection_prompt
from vmware_aria_operations_integration_sdk.ui import Spinner
from vmware_aria_operations_integration_sdk.validation.describe_checks import (
    validate_describe,
)
from vmware_aria_operations_integration_sdk.validation.input_validators import (
    ContainerRegistryValidator,
)

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
console_handler = PTKHandler()
console_handler.setFormatter(CustomFormatter())
logger.addHandler(console_handler)


def build_subdirectories(directory: str) -> None:
    """
    Parse the given directory and generates a subdirectory for every file in the current directory, then it moves each
    file inside the subdirectory. Subdirectories are ignored.

    If the given directory contains a file with a .properties extension, we exit the program

    :return: None
    """
    if not os.path.exists(directory):
        return

    content_files = [
        file
        for file in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, file))
    ]

    for file in content_files:
        file_ext = os.path.splitext(file)[1].lower()
        if file_ext == ".properties":
            logger.error(f"Found .properties file in {os.path.basename(directory)}")
            logger.info(
                f"If a {os.path.basename(directory).removesuffix('s')} requires a '.properties' file, move the {os.path.basename(directory).removesuffix('s')}"
                f"into a subdirectory inside the {directory} directory, and move the properties"
                "file to a 'resources' directory that is also inside that subdirectory."
            )
            logger.info("")
            logger.info("The result should look like this: ")
            logger.info(
                f"{directory}/myContent/myContent.{'json' if 'dashboards' == os.path.basename(directory) else 'xml'}"
            )
            logger.info(f"{directory}/myContent/resources/myContent.properties")
            logger.info(
                f"For detailed information, consult the documentation in VMware Aria Operations Integration SDK -> Guides -> Adding Content."
            )
            exit(1)

    for file in content_files:
        file_name = os.path.splitext(file)[0].lower()
        dir_path = os.path.join(directory, f"{file_name}")
        mkdir(dir_path)
        shutil.move(os.path.join(directory, file), dir_path)


def is_valid_registry(container_registry: str, **kwargs: Any) -> bool:
    try:
        if _is_docker_hub_registry_format(container_registry):
            if "registry_username" not in kwargs:
                kwargs["registry_username"] = prompt("Enter Docker Hub username: ")

            if "registry_password" not in kwargs:
                kwargs["registry_password"] = prompt("Password: ", is_password=True)
            login(**kwargs)

            container_registry = (
                container_registry
                if container_registry.startswith("docker.io")
                else f"docker.io/{container_registry}"
            )

        login(container_registry=container_registry, **kwargs)

    except LoginError:
        return False

    return True


def _is_docker_hub_registry_format(registry: Optional[str]) -> bool:
    if not registry:
        return False
    # should match namespace/repo or docker.io/namespace/repo
    # namespace must be between 4 and 30 characters long, and can only contain numbers and lowercase letters"
    # repos must contain at least two characters, can't start or end with _ . -, can't contain uppercase letters
    pattern = r"^(?:docker\.io\/[a-z0-9]{4,30}|[a-z0-9]{4,30})\/[a-z0-9]+[a-z0-9._-]*[a-z0-9]+$"

    return bool(re.match(pattern, registry))


def _tag_and_push(
    image: Image,
    container_registry_arg: Optional[str],
    config_file: str,
    manifest: dict,
    adapter_kind_key: str,
    docker_client: DockerClient,
    **kwargs: Any,
) -> tuple[str, str, str, str]:
    container_registry = container_registry_arg
    if not container_registry:
        container_registry = get_config_value(
            CONFIG_CONTAINER_REGISTRY_KEY, config_file=config_file
        )
    if not container_registry:
        container_registry = get_config_value(
            CONFIG_FALLBACK_CONTAINER_REGISTRY_KEY, config_file=config_file
        )

    # we want to keep track of the original value, so we can update it if nesessary
    original_value = container_registry

    digest = ""
    should_prompt = container_registry_arg is None
    while not digest:
        container_registry = validate_container_registry(
            adapter_kind_key,
            config_file,
            container_registry,
            should_prompt,
            **kwargs,
        )

        tag = manifest["version"] + "_" + str(time.time())

        image.tag(container_registry, tag)

        try:
            with Spinner(f"Pushing Adapter Image to {container_registry}"):
                digest = push_image(docker_client, container_registry, tag)
        except PushError as push_error:
            if should_prompt:
                logger.error(push_error.message)
            else:
                raise push_error

        # We only set the value if we are able to push the image
        if original_value != container_registry and digest:
            set_config_value(
                key=CONFIG_CONTAINER_REGISTRY_KEY,
                value=container_registry,
                config_file=config_file,
            )

        components = ContainerRegistryValidator.get_container_registry_components(
            container_registry
        )

    logger.error(components)
    return (components["domain"], components["port"], components["path"], digest)


def registry_prompt(default: str) -> str:
    return prompt(
        "Enter the full path for the container registry: ",
        default=default,
        validator=ContainerRegistryValidator("Path"),
        description="The full path of a container registry refers to the combination of domain, port, and path to a container registry.\n"
        "Example:\n"
        "'projects.registry.vmware.com:443/vmware_aria_operations_integration_sdk_mps/base-adapter:latest' breaks into:\n\n"
        "- domain: projects.registry.vmware.com\n"
        "- port: 443\n"
        "- path: vmware_aria_operations_integration_sdk_mps/base-adapter\n"
        "- tag: latest\n\n"
        "Port number is optional, and defaults to 443.\n"
        "Tag should be omitted from the full path.\n"
        "For Docker Hub repositories, simply specify the path.",
    )


def validate_container_registry(
    adapter_kind_key: str,
    config_file: str,
    container_registry: Optional[str],
    should_prompt: bool = True,
    **kwargs: Any,
) -> str:
    if should_prompt:
        default_registry_value = get_config_value(
            CONFIG_DEFAULT_CONTAINER_REGISTRY_PATH_KEY
        )
        print(
            "mp-build needs to configure a container registry to store the adapter container image.",
            "class:information",
        )
        if default_registry_value is not None:
            # The default registry should have a trailing fordward slash
            default_registry_value = (
                f"{default_registry_value}{adapter_kind_key.lower()}"
            )
            container_registry = registry_prompt(default=default_registry_value)
        else:
            container_registry = registry_prompt(default="")

        first_time = True
        while not is_valid_registry(str(container_registry), **kwargs):
            if first_time:
                print("Press Ctrl + C to cancel build", "class:information")
                first_time = False
            container_registry = registry_prompt(default=container_registry)
    else:
        if not is_valid_registry(str(container_registry), **kwargs):
            raise LoginError

    if _is_docker_hub_registry_format(container_registry) and not str(
        container_registry
    ).startswith("docker.io"):
        container_registry = f"docker.io/{container_registry}"

    return str(container_registry)


def fix_describe(describe_adapter_kind_key: Optional[str], manifest_file: str) -> Dict:
    if describe_adapter_kind_key is None:
        exit(1)
    if not selection_prompt(
        f"Update manifest.txt with adapter kind from describe.xml ('{describe_adapter_kind_key}')?",
        [(True, "Yes"), (False, "No")],
        "Select 'Yes' to update the 'manifest.txt' file and continue with the build. Select 'No' to exit without "
        "building and fix the issue manually.",
    ):
        exit(1)
    manifest = {}
    with open(manifest_file) as manifest_fd:
        # use ordered dictionary to preserve the key order in the file
        manifest = json.load(manifest_fd, object_pairs_hook=collections.OrderedDict)
    manifest["adapter_kinds"] = [describe_adapter_kind_key]
    # Rewrite the original manifest file
    with open(manifest_file, "w") as manifest_fd:
        json.dump(manifest, manifest_fd, indent=4, sort_keys=False)
    # Rewrite the manifest file in the working directory (temporary build dir)
    with open("manifest.txt", "w") as manifest_fd:
        json.dump(manifest, manifest_fd, indent=4, sort_keys=False)
    print("Wrote updated manifest.txt file.", "class:success")
    return manifest


async def build_pak_file(
    project_path: str,
    insecure_communication: bool,
    container_registry_arg: Optional[str],
    **kwargs: Any,
) -> str:
    docker_client = init()

    manifest_file = os.path.join(project_path, "manifest.txt")

    with open(manifest_file) as manifest_fd:
        manifest = json.load(manifest_fd)

    config_file = os.path.join(project_path, "config.json")
    adapter_container = AdapterContainer(project_path, docker_client)
    memory_limit = get_config_value(
        CONFIG_DEFAULT_MEMORY_LIMIT_KEY, 1024, os.path.join(project_path, "config.json")
    )
    adapter_container.start(memory_limit)
    try:
        await adapter_container.wait_for_container_startup()
        Describe.initialize(project_path, adapter_container)
        describe, resources = await Describe.get()
        validate_describe(project_path, describe)

        try:
            describe_adapter_kind_key = get_adapter_kind(describe)
        except Exception as e:
            describe_adapter_kind_key = None

        adapter_kinds = manifest.get("adapter_kinds", [])
        if len(adapter_kinds) == 0:
            logger.error(
                "Management Pack has no adapter kind specified in manifest.txt (key='adapter_kinds')."
            )
            manifest = fix_describe(describe_adapter_kind_key, manifest_file)
            adapter_kinds = manifest["adapter_kinds"]

        if len(adapter_kinds) > 1:
            logger.error(
                "The build tool does not support Management Packs with multiple adapters, but multiple adapter "
                "kinds are specified in manifest.txt (key='adapter_kinds')."
            )
            manifest = fix_describe(describe_adapter_kind_key, manifest_file)
            adapter_kinds = manifest["adapter_kinds"]
        adapter_kind_key = adapter_kinds[0]

        if (
            describe_adapter_kind_key is not None
            and describe_adapter_kind_key != adapter_kind_key
        ):
            logger.error(
                f'The \'adapter_kinds\' key in manifest.txt ("adapter_kinds": ["{adapter_kind_key}"]\') must '
                f"contain a single item matching the adapter kind key in describe.xml: "
                f"'{describe_adapter_kind_key}'."
            )
            manifest = fix_describe(describe_adapter_kind_key, manifest_file)

        try:
            with Spinner("Creating Adapter Image"):
                # The first item is the Image object for the image that was built.
                # The second item is a generator of the build logs as JSON-decoded objects.
                image, _ = build_image(docker_client, path=project_path)

            domain, port, path, digest = _tag_and_push(
                image,
                container_registry_arg,
                config_file,
                manifest,
                adapter_kind_key,
                docker_client,
                **kwargs,
            )

            # docker daemon seems to have issues when the port is specified: https://github.com/moby/moby/issues/40619
            conf_registry_field = f"{domain}:{port if port else '443'}"
            conf_repo_field = path

        finally:
            # We have to make sure the image was built, otherwise we can raise another exception
            if image:
                image.remove(force=True)

        with Spinner("Assembling Pak File"):
            adapter_dir = adapter_kind_key + "_adapter3"
            mkdir(adapter_dir)
            shutil.copytree("conf", os.path.join(adapter_dir, "conf"))
            if not os.path.exists(os.path.join(adapter_dir, "conf", "describe.xml")):
                write_describe(
                    describe, os.path.join(adapter_dir, "conf", "describe.xml")
                )
                mkdir(os.path.join(adapter_dir, "conf", "resources"))
                write_properties(
                    resources,
                    os.path.join(
                        adapter_dir, "conf", "resources", "resources.properties"
                    ),
                )

            with open(adapter_dir + ".conf", "w") as adapter_conf:
                adapter_conf.write(f"KINDKEY={adapter_kind_key}\n")
                api_version = "1.0.0"
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        request, response, elapsed_time = await send_get_to_adapter(
                            client, API_VERSION_ENDPOINT
                        )
                        if response.is_success:
                            api = json.loads(response.text)
                            api_version = (
                                f"{api['major']}.{api['minor']}.{api['maintenance']}"
                            )
                except Exception as e:
                    logger.warning(f"Could not retrieve API version: {e}")
                    api_version = "1.0.0"
                    logger.warning(f"Using default API version: {api_version}")

                adapter_conf.write(f"API_VERSION={api_version}\n")

                if insecure_communication:
                    adapter_conf.write(f"API_PROTOCOL=http\n")
                    adapter_conf.write(f"API_PORT=8080\n")
                else:
                    adapter_conf.write(f"API_PROTOCOL=https\n")
                    adapter_conf.write(f"API_PORT=443\n")

                adapter_conf.write(f"REGISTRY={conf_registry_field}\n")
                adapter_conf.write(f"REPOSITORY=/{conf_repo_field}\n")
                adapter_conf.write(f"DIGEST={digest}\n")

            eula_file = manifest["eula_file"]
            icon_file = manifest["pak_icon"]

            with zipfile.ZipFile("adapter.zip", "w") as adapter:
                zip_file(adapter, adapter_conf.name)
                zip_file(adapter, "manifest.txt")
                if eula_file:
                    zip_file(adapter, eula_file)
                if icon_file:
                    zip_file(adapter, icon_file)

                zip_dir(adapter, "resources")
                zip_dir(adapter, adapter_dir)

            rm(adapter_conf.name)
            rmdir(adapter_dir)

            name = manifest["name"] + "_" + manifest["version"]

            # Every config file in dashboards and reports should be in its own subdirectory
            build_subdirectories("content/dashboards")
            build_subdirectories("content/reports")

            pak_file = f"{name}.pak"
            with zipfile.ZipFile(pak_file, "w") as pak:
                zip_file(pak, "manifest.txt")

                pak_validation_script = manifest["pak_validation_script"]["script"]
                if pak_validation_script:
                    zip_file(pak, pak_validation_script)

                post_install_script = manifest["adapter_post_script"]["script"]
                if post_install_script:
                    zip_file(pak, post_install_script)

                pre_install_script = manifest["adapter_pre_script"]["script"]
                if pre_install_script:
                    zip_file(pak, pre_install_script)

                if icon_file:
                    zip_file(pak, icon_file)

                if eula_file:
                    zip_file(pak, eula_file)

                zip_dir(pak, "resources")
                zip_dir(pak, "content", include_empty_dirs=False)
                zip_file(pak, "adapter.zip")

                rm("adapter.zip")

                return pak_file
    finally:
        await adapter_container.stop()


def main() -> None:
    try:
        description = "Tool for building a pak file for a project."
        parser = argparse.ArgumentParser(description=description)

        parser.add_argument(
            "-V",
            "--version",
            action="version",
            version=pkg_resources.get_distribution(
                "vmware-aria-operations-integration-sdk"
            ).version,
        )

        # General options
        parser.add_argument(
            "-p",
            "--path",
            help="Path to root directory of project. Defaults to the current directory, "
            "or prompts if current directory is not a project.",
        )

        parser.add_argument(
            "--registry-tag",
            help="The full container registry tag where the container image will be stored (overwrites config file).",
            nargs="?",
            const="",
        )

        parser.add_argument(
            "--registry-username", help="The container registry username."
        )

        parser.add_argument(
            "--registry-password", help="The container registry password."
        )

        parser.add_argument(
            "-i",
            "--insecure-collector-communication",
            help="If this flag is present, communication between the collector (Cloud Proxy) and the "
            "adapter will be unencrypted. If using a custom server with this option, the server "
            "must be configured to listen on port 8080.",
            action="store_true",
        )

        parser.add_argument(
            "--no-ttl",
            help="If this flag is present, certain features dependent on having a TTL "
            "will be disabled. All arguments will need to be passed as command "
            "line options. This is useful for running mp-build on a headless "
            "build server",
            action="store_true",
        )
        parsed_args = parser.parse_args()
        project = get_project(parsed_args)
        insecure_communication = parsed_args.insecure_collector_communication
        container_registry = parsed_args.registry_tag
        registry_username = parsed_args.registry_username
        registry_password = parsed_args.registry_password
        if parsed_args.no_ttl:
            ui.TTL = False

        log_file_path = os.path.join(project.path, "logs")
        if not os.path.exists(log_file_path):
            mkdir(log_file_path)

        try:
            log_handler = RotatingFileHandler(
                os.path.join(log_file_path, "build.log"),
                # No max size, but we'll roll over immediately so each build has its own file
                maxBytes=0,
                backupCount=5,
            )
            logging.basicConfig(
                format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
                datefmt="%H:%M:%S",
                handlers=[log_handler],
                level=logging.DEBUG,
            )
            log_handler.doRollover()
        except Exception as e:
            logger.warning(f"Unable to save logs to {log_file_path}: {e}")

        project_dir = project.path
        # We want to store pak files in the build dir
        build_dir = os.path.join(project_dir, "build")
        # Any artifacts for generating the pak file should be stored here
        temp_dir = os.path.join(build_dir, "tmp")

        # Clean old builds
        if os.path.exists(build_dir):
            rmdir(build_dir)

        mkdir(build_dir)

        try:
            # TODO: remove this copy and add logic to zip files from the source
            shutil.copytree(
                project.path,
                temp_dir,
                ignore=shutil.ignore_patterns(
                    "build",
                    "logs",
                    "Dockerfile",
                    "adapter_requirements",
                    "commands.cfg",
                    ".git",
                    ".gitignore",
                ),
                dirs_exist_ok=True,
            )

            os.chdir(temp_dir)

            pak_file = asyncio.run(
                build_pak_file(
                    project_dir,
                    insecure_communication,
                    container_registry,
                    registry_username=registry_username,
                    registry_password=registry_password,
                )
            )

            if os.path.exists(os.path.join(build_dir, pak_file)):
                # NOTE: we could ask the user if they want to overwrite the current file instead of always deleting it
                logger.debug("Deleting old pak file")
                rm(os.path.join(build_dir, pak_file))

            shutil.move(pak_file, build_dir)
            print("Build Succeeded", "class:success")
        finally:
            # There is a small probability that the temp dir doesn't exist
            if os.path.exists(temp_dir):
                logger.debug(f"Deleting directory: '{temp_dir}'")
                if os.getcwd() == temp_dir:
                    # Change working directory to the build directory, otherwise we won't be able to delete the
                    # directory in Windows based systems
                    os.chdir(project_dir)
                rmdir(temp_dir)
    except DockerWrapperError as error:
        logger.error("Unable to build pak file")
        logger.error(error.message)
        logger.info(error.recommendation)
        exit(1)
    except KeyboardInterrupt:
        logger.debug("Ctrl-C pressed by user")
        print("")
        logger.info("Build cancelled")
        exit(1)
    except SystemExit as system_exit:
        if system_exit.code != 0:
            logger.error("Unable to build pak file")
        exit(system_exit.code)
    except Exception as exception:
        logger.error("Unexpected exception occurred while trying to build pak file")
        logger.error(exception)
        traceback.print_tb(exception.__traceback__)
        exit(1)


if __name__ == "__main__":
    main()
