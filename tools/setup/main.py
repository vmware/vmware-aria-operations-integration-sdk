import json
import os
from shutil import copyfile
from colorama import init, Fore, Style


def is_directory_or_not_existing(p: str):
    if not os.path.exists(p):
        return True
    if os.path.isfile(p):
        print(Fore.RED + "ERROR: Path must be a directory.")
        return False
    return True


def is_file(p: str):
    if os.path.isfile(p):
        return True
    else:
        print(Fore.RED + "ERROR: Specified path is not a file.")
        return False


def not_blank(p: str):
    # Empty strings are falsy
    return p.strip()


def main():
    init()

    path = input_with_retry("Path to base: ", is_directory_or_not_existing)
    mkdir(path)

    paths = []
    if os.path.isfile("projects"):
        with open("projects", "r") as projects:
            paths = projects.readlines()
    if path not in paths:
        with open("projects", "a") as projects:
            projects.write(f"{path}\n")

    content_dir = mkdir(path, "content")
    dashboard_dir = mkdir(content_dir, "dashboards")
    files_dir = mkdir(content_dir, "files")
    reports_dir = mkdir(content_dir, "reports")

    resources_dir = mkdir(path, "resources")
    resources_file = os.path.join(resources_dir, "resources.properties")
    name = input("Display name: ")
    description = input("Description: ")
    vendor = input("Your company: ")
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

    print("")
    if (input("Do you have a EULA (y/N)? ") or "N").lower() != "y":
        print(
            "EULA can be added later by setting the 'eula_file' key in 'manifest.txt' and adding the eula file to the root adapter directory.")
        eula_file = ""
    else:
        eula_file = input_with_retry("What is the path to the EULA file? ", is_file)
        copyfile(eula_file, path)

    # TODO: refactor similar steps
    print("")
    if (input("Do you have an icon for the management pack (y/N)? ") or "N").lower() != "y":
        print(
            "An icon can be added later by setting the 'pak_icon' key in 'manifest.txt and adding the icon file to the root adapter directory.'")
        icon_file = ""
    else:
        icon_file = input_with_retry("What is the path to the icon file? ", is_file)
        copyfile(icon_file, path)

    manifest_file = os.path.join(path, "manifest.txt")
    manifest = {
        "display_name": "DISPLAY_NAME",
        "name": "".join(name.split(" ")),
        "description": "DESCRIPTION",
        "version": "1.0.0",
        "vcops_minimum_version": "8.1.1",
        "disk_space_required": 500,
        "run_scripts_on_all_nodes": "true",
        "eula_file": eula_file,
        "platform": [
            "Linux Non-VA",
            "Linux VA"
        ],
        "vendor": "VENDOR",
        "pak_icon": icon_file,
        "pak_validation_script": {
            "script": ""
        },
        "adapter_pre_script": {
            "script": ""
        },
        "adapter_post_script": {
            "script": ""
        },
        "adapters": [
            "adapter.zip"
        ],
        "adapter_kinds": [
            "".join(name.split(" "))
        ],
        "license_type": ""
    }
    with open(manifest_file, "w") as manifest_fd:
        json.dump(manifest, manifest_fd, indent=4)

    print("")

    supported_languages = ["python"]
    print(f"Supported languages are: {supported_languages}")
    language = input_with_retry("What language would you like to use? ", lambda x: x.lower() in supported_languages).lower()

    if language == "python":
        app_dir = mkdir(path, "app")


def input_with_retry(message: str, validation_function):
    while True:
        value = input(message)
        if validation_function(value):
            return value


def mkdir(basepath, *paths):
    path = os.path.join(basepath, *paths)
    if not os.path.exists(path):
        os.mkdir(path, 0o755)
    return path


if __name__ == '__main__':
    main()
