import json
import os
import shutil
import tempfile
import time
import zipfile

from shutil import copyfile
from PyInquirer import style_from_dict, Token, prompt

from common.filesystem import zip_dir, mkdir


def main():
    paths = []
    if os.path.isfile("projects"):
        with open("projects", "r") as projects:
            paths = [line.strip() for line in projects.readlines()]

    style = style_from_dict({
        Token.QuestionMark: "#E91E63 bold",
        Token.Selected: "#673AB7 bold",
        Token.Instruction: "",  # default
        Token.Answer: "#2196f3 bold",
        Token.Question: "",
    })

    # TODO: use PyInquirer for other script?
    questions = [
        {
            "type": "list",
            "name": "project",
            "message": "Which project?",
            "choices": paths + ["other"],
            "filter": lambda val: val.lower()
        },
        {
            "type": "input",
            "name": "path",
            "message": "what is the path to the project?",
            "validate": lambda path: (os.path.isdir(path) and os.path.isfile(os.path.join(path, "manifest.txt"))) or "Path must be a valid Management Pack project directory",
            "when": lambda answers: answers["project"] == "other"
        },
    ]

    answers = prompt(questions, style=style)

    path = answers["project"]
    if path == "other":
        path = answers["path"]

    os.chdir(path)

    with open("manifest.txt") as manifest_file:
        manifest = json.load(manifest_file)

    # TODO: The repo and project need to be configurable.
    docker_image_tag = "harbor-repo.vmware.com/tvs_vrops_python_sdk_dev/" + manifest["name"].lower() + ":" + manifest["version"] + "_" + str(time.time())

    os.system(f"docker build --no-cache . --tag {docker_image_tag}")
    os.system(f"docker push {docker_image_tag}")

    name = "PAKFILE_NAME"
    adapter_dir = manifest["name"] + "_adapter3"
    mkdir(adapter_dir)
    shutil.copytree("conf", os.path.join(adapter_dir, "conf"))

    with open(adapter_dir + ".conf", "w") as docker_conf:
        docker_conf.write(f"KINDKEY={manifest['name']}\n")
        docker_conf.write(f"ImageTag={docker_image_tag}\n")

    with zipfile.ZipFile("adapter.zip", "w") as adapter:

        adapter.write(docker_conf.name, compress_type=zipfile.ZIP_DEFLATED)
        zip_dir(adapter, adapter_dir)

    os.remove(docker_conf.name)
    shutil.rmtree(adapter_dir)

    with zipfile.ZipFile(f"{name}.pak", "w") as pak:
        pak.write("manifest.txt", compress_type=zipfile.ZIP_DEFLATED)

        pak_validation_script = manifest["pak_validation_script"]["script"]
        if pak_validation_script:
            pak.write(pak_validation_script, compress_type=zipfile.ZIP_DEFLATED)

        post_install_script = manifest["adapter_post_script"]["script"]
        if post_install_script:
            pak.write(post_install_script, compress_type=zipfile.ZIP_DEFLATED)

        pre_install_script = manifest["adapter_pre_script"]["script"]
        if pre_install_script:
            pak.write(pre_install_script, compress_type=zipfile.ZIP_DEFLATED)

        icon_file = manifest["pak_icon"]
        if icon_file:
            pak.write(icon_file, compress_type=zipfile.ZIP_DEFLATED)

        eula_file = manifest["eula_file"]
        if eula_file:
            pak.write(eula_file, compress_type=zipfile.ZIP_DEFLATED)

        zip_dir(pak, "resources")
        zip_dir(pak, "content")
        pak.write("adapter.zip", compress_type=zipfile.ZIP_DEFLATED)

    os.remove("adapter.zip")


if __name__ == "__main__":
    main()
