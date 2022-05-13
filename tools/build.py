import argparse
import json
import os
import shutil
import time
import zipfile

from common.config import get_config_value
from common.docker_wrapper import login, init, push_image, build_image, BuildError, PushError, InitError
from common.filesystem import zip_dir, mkdir, zip_file, rmdir
from common.project import get_project


def get_digest(response) -> str:
    """
    Get the images digest by parsing the server response.
    An alternate method of parsing the digest from an image would be to
    parse the attributes of an image and then check if the image has repoDigests
    attribute, then we could parse the repo digest (different from digest) to get the digest.


    :param response: A Stream that of dictionaries with information about the image being pushed
    :return: A string version of the SHA256 digest
    """
    for line in response:
        if 'aux' in line:
            try:
                return line['aux']['Digest']
            except KeyError:
                print("ERROR digest was not found in response from registry")
                exit(1)

        elif 'errorDetail' in line:
            print("ERROR when pushing image to docker registry")
            print("repo: {repo}")
            print(line["errorDetail"]["message"])
            exit(1)
    pass


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
            print(
                f"If a {os.path.basename(directory).removesuffix('s')} requires a '.properties' file, move the {os.path.basename(directory).removesuffix('s')}"
                f"into a subdirectory inside the {directory} directory, and move the properties"
                "file to a 'resources' directory that is also inside that subdirectory.")
            print("")
            print("The result should look like this: ")
            print(f"{directory}/myContent/myContent.{'json' if 'dashboards' == os.path.basename(directory) else 'xml'}")
            print(f"{directory}/myContent/resources/myContent.properties")
            print(
                f"For detailed information, consult the documentation in vROps Integration SDK -> Guilds -> Adding Content.")
            exit(1)

    for file in content_files:
        file_name = os.path.splitext(file)[0].lower()
        dir_path = os.path.join(directory, f"{file_name}")
        os.mkdir(dir_path)
        shutil.move(os.path.join(directory, file), dir_path)


def main():
    description = "Tool for building a pak file for a project."
    parser = argparse.ArgumentParser(description=description)

    # General options
    parser.add_argument("-p", "--path", help="Path to root directory of project. Defaults to the current directory, "
                                             "or prompts if current directory is not a project.")

    global project
    project = get_project(parser.parse_args())
    # We want to store pak files in the build dir
    build_dir = os.path.join(project["path"], 'build')
    # Any artifacts for generating the pak file should be stored here
    temp_dir = os.path.join(build_dir, 'tmp')

    if not os.path.exists(build_dir):
        mkdir(build_dir)

    # TODO: remove this copy and add the addecuate logic to zip files from the source
    shutil.copytree(
        project["path"],
        temp_dir,
        ignore=shutil.ignore_patterns("build", "logs", "Dockerfile", "adapter_requirements", "commands.cfg")
    )

    os.chdir(temp_dir)

    try:

        docker_client = init()

        with open("manifest.txt") as manifest_file:
            manifest = json.load(manifest_file)

        repo = get_config_value("docker_repo", "tvs")
        registry_url = login()

        tag = manifest["name"].lower() + ":" + manifest["version"] + "_" + str(time.time())
        registry_tag = f"{registry_url}/{repo}/{tag}"
        try:
            adapter, adapter_logs = build_image(docker_client, path=project["path"], tag=tag)
            adapter.tag(registry_tag)

            digest = push_image(docker_client, registry_tag)
        finally:
            docker_client.images.remove(registry_tag)

        adapter_dir = manifest["name"] + "_adapter3"
        mkdir(adapter_dir)
        shutil.copytree("conf", os.path.join(adapter_dir, "conf"))

        with open(adapter_dir + ".conf", "w") as docker_conf:
            docker_conf.write(f"KINDKEY={manifest['name']}\n")
            # TODO: Need a way to determine this
            docker_conf.write(f"API_VERSION=1.0.0\n")
            # docker_conf.write(f"ImageTag={registry_tag}\n")
            docker_conf.write(f"REGISTRY={registry_url}\n")
            # TODO switch to this repository by default? /vrops_internal_repo/dockerized/aggregator/sandbox
            docker_conf.write(
                f"REPOSITORY=/{repo}/{manifest['name'].lower()}\n")  # TODO: replace this with a more optimal
            # solution, since this might be unique to harbor
            docker_conf.write(f"DIGEST={digest}\n")

        eula_file = manifest["eula_file"]
        icon_file = manifest["pak_icon"]

        with zipfile.ZipFile("adapter.zip", "w") as adapter:
            zip_file(adapter, docker_conf.name)
            zip_file(adapter, "manifest.txt")
            if eula_file:
                zip_file(adapter, eula_file)
            if icon_file:
                zip_file(adapter, icon_file)

            zip_dir(adapter, "resources")
            zip_dir(adapter, adapter_dir)

        os.remove(docker_conf.name)
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

            shutil.move(pak_file, build_dir)
    except (BuildError, PushError, InitError):
        print("Unable to build pak file")
    finally:
        rmdir(temp_dir)


# This function might needed to calculate path later
# def path(*path):
#     actual_path = os.path.join(project["path"], *path)
#     return actual_path
#

if __name__ == "__main__":
    main()
