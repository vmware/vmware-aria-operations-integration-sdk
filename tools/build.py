import argparse
import json
import logging
import os
import shutil
import time
import traceback
import zipfile

from prompt_toolkit import prompt
from common.config import get_config_value, set_config_value
from common.docker_wrapper import login, init, push_image, build_image, DockerWrapperError
from common.filesystem import zip_dir, mkdir, zip_file, rmdir
from common.project import get_project
from common.ui import print_formatted as print
from common import filesystem
from common.validation.input_validators import NotEmptyValidator

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = logging.StreamHandler()
logger.addHandler(consoleHandler)


def build_subdirectories(directory: str):
    """
    Parse the given directory and generates a subdirectory for every file in the current directory, then it moves each
    file inside the subdirectory. Subdirectories are ignored.

    If the given directory contains a file with a .properties extension, we exit the program

    :return: None
    """
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
            logger.info(f"{directory}/myContent/myContent.{'json' if 'dashboards' == os.path.basename(directory) else 'xml'}")
            logger.info(f"{directory}/myContent/resources/myContent.properties")
            logger.info(
                f"For detailed information, consult the documentation in vROps Integration SDK -> Guides -> Adding Content.")
            exit(1)

    for file in content_files:
        file_name = os.path.splitext(file)[0].lower()
        dir_path = os.path.join(directory, f"{file_name}")
        os.mkdir(dir_path)
        shutil.move(os.path.join(directory, file), dir_path)


def build_pak_file(project_path, insecure_communication):
    docker_client = init()

    with open("manifest.txt") as manifest_file:
        manifest = json.load(manifest_file)

    # We should ask the user for this before we populate them with default values
    # Default values are only accessible for authorize memebers, so we might want to add a message about it
    config_file = os.path.join(project_path, "config.json")

    adapter_kinds = manifest["adapter_kinds"]
    if len(adapter_kinds) == 0:
        logger.error("Management Pack has no adapter kind specified in manifest.txt (key='adapter_kinds').")
        exit(1)
    if len(adapter_kinds) > 1:
        logger.error("The build tool does not support Management Packs with multiple adapters, but multiple adapter "
                     "kinds are specified in manifest.txt (key='adapter_kinds').")
        exit(1)
    adapter_kind_key = adapter_kinds[0]

    registry_host = get_config_value("docker_registry_host", config_file=config_file)
    repo_path = get_config_value("docker_repo_path", config_file=config_file)
    repo_name = get_config_value("docker_repo_name", config_file=config_file)

    if registry_host is None:
        print("mp-build would like to configure a docker registry to push the conatiner image related to this project")
        registry_host = prompt("Enter the registry host: ", default="docker.io", validator=NotEmptyValidator("Host"))
        repo_path = prompt("Enter enter repository path: ", validator=NotEmptyValidator("Path"))
        repo_name = prompt("Enter enter repository name: ", default=adapter_kind_key.lower(), validator= NotEmptyValidator("Name"))


        # TODO: add special case where there is no registry path
        set_config_value(key="docker_registry_host", value=registry_host, config_file=config_file)
        set_config_value(key="docker_repo_path", value=repo_path, config_file=config_file)
        set_config_value(key="docker_repo_name", value=repo_name, config_file=config_file)

    login(registry_host)

    tag = manifest["version"] + "_" + str(time.time())

    conf_repo_field = f"{repo_path}/{repo_name}"

    # docker daemon seems to have issues when the port is specified: https://github.com/moby/moby/issues/40619
    conf_registry_field = registry_host

    registry_tag = f"{conf_registry_field}/{conf_repo_field}:{tag}"
    logger.debug(f"registry tag: {registry_tag}")

    try:
        adapter, adapter_logs = build_image(docker_client, path=project_path, tag=f"{repo_name}:{tag}")
        adapter.tag(registry_tag)

        digest = push_image(docker_client, registry_tag)
    finally:
        # We have to make sure the image was built, otherwise we can raise another exception
        if docker_client.images.list(registry_tag):
            docker_client.images.remove(registry_tag)

    adapter_dir = adapter_kind_key + "_adapter3"
    mkdir(adapter_dir)
    shutil.copytree("conf", os.path.join(adapter_dir, "conf"))

    with open(adapter_dir + ".conf", "w") as adapter_conf:
        adapter_conf.write(f"KINDKEY={adapter_kind_key}\n")
        # TODO: Need a way to determine the api version
        adapter_conf.write(f"API_VERSION=1.0.0\n")

        if insecure_communication:
            adapter_conf.write(f"API_PROTOCOL=http\n")
            adapter_conf.write(f"API_PORT=8080\n")
        else:
            adapter_conf.write(f"API_PROTOCOL=https\n")
            adapter_conf.write(f"API_PORT=443\n")

        adapter_conf.write(f"REGISTRY={conf_registry_field}\n")
        # TODO switch to this repository by default? /vrops_internal_repo/dockerized/aggregator/sandbox
        # TODO: replace this with a more optimal solution, since this might be unique to harbor
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

    os.remove(adapter_conf.name)
    shutil.rmtree(adapter_dir)

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

        os.remove("adapter.zip")

        return pak_file


def main():
    try:
        description = "Tool for building a pak file for a project."
        parser = argparse.ArgumentParser(description=description)

        # General options
        parser.add_argument("-p", "--path",
                            help="Path to root directory of project. Defaults to the current directory, "
                                 "or prompts if current directory is not a project.")

        parser.add_argument("-i", "--insecure-collector-communication",
                            help="If this flag is present, communication between the vROps collector and the adapter "
                                 "will be unencrypted. If using a custom server with this option, the server must be "
                                 "configured to listen on port 8080.",
                            action="store_true")
        parsed_args = parser.parse_args()
        project = get_project(parsed_args)
        insecure_communication = parsed_args.insecure_collector_communication

        log_file_path = os.path.join(project.path, 'logs')
        if not os.path.exists(log_file_path):
            filesystem.mkdir(log_file_path)

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

        if not os.path.exists(build_dir):
            mkdir(build_dir)

        try:
            # TODO: remove this copy and add logic to zip files from the source
            shutil.copytree(
                project.path,
                temp_dir,
                ignore=shutil.ignore_patterns("build", "logs", "Dockerfile", "adapter_requirements", "commands.cfg"),
                dirs_exist_ok=True
            )

            os.chdir(temp_dir)

            pak_file = build_pak_file(project_dir, insecure_communication)

            if os.path.exists(os.path.join(build_dir, pak_file)):
                # NOTE: we could ask the user if they want to overwrite the current file instead of always deleting it
                logger.debug("Deleting old pak file")
                os.remove(os.path.join(build_dir, pak_file))

            shutil.move(pak_file, build_dir)
            print("Build succeeded", "fg:ansigreen")
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
        exit(system_exit.code)
    except Exception as exception:
        logger.error("Unexpected exception occurred while trying to build pak file")
        traceback.print_tb(exception.__traceback__)
        exit(1)


if __name__ == "__main__":
    main()
