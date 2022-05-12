import argparse
import json
import os
import shutil
import time
import zipfile

import docker

from common.config import get_config_value
from common.docker_wrapper import login, init, push_image, build_image
from common.filesystem import zip_dir, mkdir, zip_file
from common.project import get_project


def main():
    description = "Tool for building a pak file for a project."
    parser = argparse.ArgumentParser(description=description)

    docker_client = init()

    # General options
    parser.add_argument("-p", "--path", help="Path to root directory of project. Defaults to the current directory, "
                                             "or prompts if current directory is not a project.")

    project = get_project(parser.parse_args())
    os.chdir(project["path"])

    with open("manifest.txt") as manifest_file:
        manifest = json.load(manifest_file)

    repo = get_config_value("docker_repo", "tvs")
    registry_url = login()

    tag = manifest["name"].lower() + ":" + manifest["version"] + "_" + str(time.time())
    registry_tag = f"{registry_url}/{repo}/{tag}"
    adapter, adapter_logs = build_image(docker_client, path=project["path"], tag=tag)
    # TODO: handle BuildError
    adapter.tag(registry_tag)

    digest = push_image(docker_client, registry_tag)
    # TODO: handle exception by deleting all generated artifacts

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
        docker_conf.write(f"REPOSITORY=/{repo}/{manifest['name'].lower()}\n")  # TODO: replace this with a more optimal
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
        zip_dir(adapter, "content")
        zip_dir(adapter, adapter_dir)

    os.remove(docker_conf.name)
    shutil.rmtree(adapter_dir)

    name = manifest["name"] + "_" + manifest["version"]

    with zipfile.ZipFile(f"{name}.pak", "w") as pak:
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


if __name__ == "__main__":
    main()
