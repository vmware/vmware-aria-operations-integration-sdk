#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import argparse
import asyncio
import collections
import json
import logging
import os
import shutil
import time
import traceback
import zipfile

import httpx

from vmware_aria_operations_integration_sdk.adapter_container import AdapterContainer
from vmware_aria_operations_integration_sdk.config import get_config_value, set_config_value
from vmware_aria_operations_integration_sdk.constant import API_VERSION_ENDPOINT
from vmware_aria_operations_integration_sdk.containerized_adapter_rest_api import send_get_to_adapter
from vmware_aria_operations_integration_sdk.describe import get_adapter_kind, Describe, write_describe
from vmware_aria_operations_integration_sdk.docker_wrapper import login, init, push_image, build_image, \
    DockerWrapperError, LoginError
from vmware_aria_operations_integration_sdk.filesystem import zip_dir, mkdir, zip_file, rmdir, rm
from vmware_aria_operations_integration_sdk.logging_format import PTKHandler, CustomFormatter
from vmware_aria_operations_integration_sdk.project import get_project
from vmware_aria_operations_integration_sdk.propertiesfile import write_properties
from vmware_aria_operations_integration_sdk.ui import print_formatted as print, prompt, selection_prompt, Spinner
from vmware_aria_operations_integration_sdk.validation.describe_checks import validate_describe
from vmware_aria_operations_integration_sdk.validation.input_validators import NotEmptyValidator

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = PTKHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)


def build_subdirectories(directory: str):
    """
    Parse the given directory and generates a subdirectory for every file in the current directory, then it moves each
    file inside the subdirectory. Subdirectories are ignored.

    If the given directory contains a file with a .properties extension, we exit the program

    :return: None
    """
    if not os.path.exists(directory):
        return

    content_files = [file for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]

    for file in content_files:
        file_ext = os.path.splitext(file)[1].lower()
        if file_ext == ".properties":
            logger.error(f"Found .properties file in {os.path.basename(directory)}")
            logger.info(
                f"If a {os.path.basename(directory).removesuffix('s')} requires a '.properties' file, move the {os.path.basename(directory).removesuffix('s')}"
                f"into a subdirectory inside the {directory} directory, and move the properties"
                "file to a 'resources' directory that is also inside that subdirectory.")
            logger.info("")
            logger.info("The result should look like this: ")
            logger.info(
                f"{directory}/myContent/myContent.{'json' if 'dashboards' == os.path.basename(directory) else 'xml'}")
            logger.info(f"{directory}/myContent/resources/myContent.properties")
            logger.info(
                f"For detailed information, consult the documentation in VMware Aria Operations Integration SDK -> Guides -> Adding Content.")
            exit(1)

    for file in content_files:
        file_name = os.path.splitext(file)[0].lower()
        dir_path = os.path.join(directory, f"{file_name}")
        mkdir(dir_path)
        shutil.move(os.path.join(directory, file), dir_path)


def get_registry_components(docker_registry: str) -> (str, str):
    components = docker_registry.split('/')
    host = components[0]
    path = "/".join(components[1:])
    return host, path


def is_valid_registry(docker_registry) -> bool:
    try:
        login(docker_registry)
    except LoginError:
        return False

    return True


def registry_prompt(default):
    return prompt("Enter the tag for the Docker registry: ",
                  default=default,
                  validator=NotEmptyValidator("Host"),
                  description="The tag of a Docker registry is used to login into the Docker registry. the tag is composed of\n"
                              "three parts: domain, port, and path. For example:\n"
                              "projects.registry.vmware.com:443/vmware_aria_operations_integration_sdk_mps/base-adapter breaks into\n"
                              "domain: projects.registry.vmware.com\n"
                              "port: 443\n"
                              "path: vmware_aria_operations_integration_sdk_mps/base-adapter\n"
                              "Domain is optional, and defaults to Docker Hub (docker.io)\n"
                              "Port number is optional, and defaults to 443."
                  )


def get_docker_registry(adapter_kind_key, config_file):
    docker_registry = get_config_value("docker_registry", config_file=config_file)

    original_value = docker_registry
    if docker_registry is None:
        print("mp-build needs to configure a Docker registry to store the adapter container image.",
              "class:information")
        docker_registry = registry_prompt(
            default=f"harbor-repo.vmware.com/vmware_aria_operations_integration_sdk_mps/{adapter_kind_key.lower()}")

    first_time = True
    while not is_valid_registry(docker_registry):
        if first_time:
            print("Press Ctrl + C to cancel build", "class:information")
            first_time = False
        docker_registry = registry_prompt(default=docker_registry)

    if original_value != docker_registry:
        set_config_value(key="docker_registry", value=docker_registry, config_file=config_file)

    return docker_registry


def fix_describe(describe_adapter_kind_key, manifest_file):
    if describe_adapter_kind_key is None:
        exit(1)
    if not selection_prompt(
            f"Update manifest.txt with adapter kind from describe.xml ('{describe_adapter_kind_key}')?",
            [(True, "Yes"), (False, "No")],
            "Select 'Yes' to update the 'manifest.txt' file and continue with the build. Select 'No' to exit without "
            "building and fix the issue manually."):
        exit(1)
    with open(manifest_file) as manifest_fd:
        # use ordered dictionary to preserve the key order in the file
        manifest = json.load(manifest_fd, object_pairs_hook=collections.OrderedDict)
    manifest["adapter_kinds"] = [describe_adapter_kind_key]
    with open(manifest_file, "w") as manifest_fd:
        json.dump(manifest, manifest_fd, indent=4, sort_keys=False)
    print("Wrote updated manifest.txt file.", "class:success")
    return manifest


async def build_pak_file(project_path, insecure_communication):
    docker_client = init()

    manifest_file = os.path.join(project_path, "manifest.txt")

    with open(manifest_file) as manifest_fd:
        manifest = json.load(manifest_fd)

    config_file = os.path.join(project_path, "config.json")
    adapter_container = AdapterContainer(project_path)
    memory_limit = get_config_value("default_memory_limit", 1024, os.path.join(project_path, "config.json"))
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
            logger.error("Management Pack has no adapter kind specified in manifest.txt (key='adapter_kinds').")
            manifest = fix_describe(describe_adapter_kind_key, manifest_file)
            adapter_kinds = manifest["adapter_kinds"]

        if len(adapter_kinds) > 1:
            logger.error("The build tool does not support Management Packs with multiple adapters, but multiple adapter "
                         "kinds are specified in manifest.txt (key='adapter_kinds').")
            manifest = fix_describe(describe_adapter_kind_key, manifest_file)
            adapter_kinds = manifest["adapter_kinds"]
        adapter_kind_key = adapter_kinds[0]

        if describe_adapter_kind_key is not None and describe_adapter_kind_key != adapter_kind_key:
            logger.error(f"The 'adapter_kinds' key in manifest.txt (\"adapter_kinds\": [\"{adapter_kind_key}\"]') must "
                         f"contain a single item matching the adapter kind key in describe.xml: "
                         f"'{describe_adapter_kind_key}'.")
            manifest = fix_describe(describe_adapter_kind_key, manifest_file)

        # We should ask the user for this before we populate them with default values
        # Default values are only accessible for authorize members, so we might want to add a message about it
        docker_registry = get_docker_registry(adapter_kind_key, config_file)

        tag = manifest["version"] + "_" + str(time.time())

        conf_registry_field, conf_repo_field = get_registry_components(docker_registry)

        # docker daemon seems to have issues when the port is specified: https://github.com/moby/moby/issues/40619

        registry_tag = f"{docker_registry}:{tag}"
        logger.debug(f"registry tag: {registry_tag}")

        try:
            with Spinner("Creating Adapter Image"):
                build_image(docker_client, path=project_path, tag=f"{registry_tag}")

            with Spinner(f"Pushing Adapter Image to {registry_tag}"):
                digest = push_image(docker_client, registry_tag)
        finally:
            # We have to make sure the image was built, otherwise we can raise another exception
            if docker_client.images.list(registry_tag):
                docker_client.images.remove(registry_tag)

        with Spinner("Assembling Pak File"):
            adapter_dir = adapter_kind_key + "_adapter3"
            mkdir(adapter_dir)
            shutil.copytree("conf", os.path.join(adapter_dir, "conf"))
            if not os.path.exists(os.path.join(adapter_dir, "conf", "describe.xml")):
                write_describe(describe, os.path.join(adapter_dir, "conf", "describe.xml"))
                mkdir(os.path.join(adapter_dir, "conf", "resources"))
                write_properties(resources, os.path.join(adapter_dir, "conf", "resources", "resources.properties"))

            with open(adapter_dir + ".conf", "w") as adapter_conf:
                adapter_conf.write(f"KINDKEY={adapter_kind_key}\n")
                api_version = "1.0.0"
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        request, response, elapsed_time = await send_get_to_adapter(client, API_VERSION_ENDPOINT)
                        if response.is_success:
                            api = json.loads(response.text)
                            api_version = f"{api['major']}.{api['minor']}.{api['maintenance']}"
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
                zip_dir(pak, "content")
                zip_file(pak, "adapter.zip")

                rm("adapter.zip")

                return pak_file
    finally:
        await adapter_container.stop()


def main():
    try:
        description = "Tool for building a pak file for a project."
        parser = argparse.ArgumentParser(description=description)

        # General options
        parser.add_argument("-p", "--path",
                            help="Path to root directory of project. Defaults to the current directory, "
                                 "or prompts if current directory is not a project.")

        parser.add_argument("-i", "--insecure-collector-communication",
                            help="If this flag is present, communication between the collector (Cloud Proxy) and the "
                                 "adapter will be unencrypted. If using a custom server with this option, the server "
                                 "must be configured to listen on port 8080.",
                            action="store_true")
        parsed_args = parser.parse_args()
        project = get_project(parsed_args)
        insecure_communication = parsed_args.insecure_collector_communication

        log_file_path = os.path.join(project.path, 'logs')
        mkdir(log_file_path)

        try:
            logging.basicConfig(filename=os.path.join(log_file_path, "build.log"),
                                filemode="a",
                                format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
                                datefmt="%H:%M:%S",
                                level=logging.DEBUG)
        except Exception:
            logger.warning(f"Unable to save logs to {log_file_path}")

        project_dir = project.path
        # We want to store pak files in the build dir
        build_dir = os.path.join(project_dir, 'build')
        # Any artifacts for generating the pak file should be stored here
        temp_dir = os.path.join(build_dir, 'tmp')

        # Clean old builds
        if os.path.exists(build_dir):
            rmdir(build_dir)

        mkdir(build_dir)

        try:
            # TODO: remove this copy and add logic to zip files from the source
            shutil.copytree(
                project.path,
                temp_dir,
                ignore=shutil.ignore_patterns("build", "logs", "Dockerfile", "adapter_requirements", "commands.cfg",
                                              ".git", ".gitignore"),
                dirs_exist_ok=True
            )

            os.chdir(temp_dir)

            pak_file = asyncio.run(build_pak_file(project_dir, insecure_communication))

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
        logger.error("Unable to build pak file")
        exit(system_exit.code)
    except Exception as exception:
        logger.error("Unexpected exception occurred while trying to build pak file")
        logger.error(exception)
        traceback.print_tb(exception.__traceback__)
        exit(1)


if __name__ == "__main__":
    main()
