import json
import os
from shutil import copy

from prompt_toolkit import prompt
from prompt_toolkit.completion.filesystem import PathCompleter

import common.constant as constant
import templates.java as java
import templates.powershell as powershell
from common.config import get_config_value
from common.filesystem import get_absolute_project_directory, get_root_directory, mkdir
from common.project import Project, record_project
from common.ui import print_formatted as print
from common.ui import selection_prompt
from common.validators import NewProjectDirectoryValidator, NotEmptyValidator, AdapterKeyValidator, EulaValidator, \
    ImageValidator


def main():
    get_root_directory()

    path = prompt(
        "Enter a path for the project (where code for collection, metadata, and content reside): ",
        validator=NewProjectDirectoryValidator("Path"),
        validate_while_typing=False,
        completer=PathCompleter(),
        complete_in_thread=True)

    name = prompt("Management pack display name: ", validator=NotEmptyValidator("Display name"))
    adapter_key = prompt("Management pack adapter key: ",
                         validator=AdapterKeyValidator("Adapter key"),
                         default=AdapterKeyValidator.default(name))
    description = prompt("Management pack description: ", validator=NotEmptyValidator("Description"))
    vendor = prompt("Management pack vendor: ", validator=NotEmptyValidator("Vendor"))
    eula_file = prompt("Enter a path to a EULA text file, or leave blank for no EULA: ",
                       validator=EulaValidator(),
                       validate_while_typing=False,
                       completer=PathCompleter(),
                       complete_in_thread=True)
    if eula_file == "":
        print("A EULA can be added later by editing the default 'eula.txt' file.")
    icon_file = prompt("Enter a path to the management pack icon file, or leave blank for no icon: ",
                       validator=ImageValidator(),
                       validate_while_typing=False,
                       completer=PathCompleter(),
                       complete_in_thread=True)
    if icon_file == "":
        print("An icon can be added later by setting the 'pak_icon' key in 'manifest.txt' to the icon file "
              "name and adding the icon file to the root project directory.")

    language = selection_prompt("Select a language for the adapter.",
                                items=[("python", "Python"),
                                       ("java", "Java", "Unavailable for alpha release"),
                                       ("powershell", "PowerShell", "Unavailable for alpha release")])

    # create project_directory
    mkdir(path)

    project = Project(path)
    record_project(project.__dict__)

    content_dir = mkdir(path, "content")
    conf_dir = mkdir(path, "conf")
    dashboard_dir = mkdir(content_dir, "dashboards")
    files_dir = mkdir(content_dir, "files")
    reports_dir = mkdir(content_dir, "reports")

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

    if not eula_file:
        eula_file = "eula.txt"
        with open(os.path.join(path, eula_file), "w") as eula_fd:
            # Note: vROps requires a EULA file, and it must not be blank.
            eula_fd.write("There is no EULA associated with this Management Pack.")
    else:
        copy(eula_file, path)
        eula_file = os.path.basename(eula_file)

    if not icon_file:
        icon_file = ""
    else:
        copy(icon_file, path)
        icon_file = os.path.basename(icon_file)

    manifest_file = os.path.join(path, "manifest.txt")
    manifest = {
        "display_name": "DISPLAY_NAME",
        "name": adapter_key,
        "description": "DESCRIPTION",
        "version": "1.0.0",
        "vcops_minimum_version": "8.7.1",
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
            adapter_key
        ],
        "license_type": ""
    }
    with open(manifest_file, "w") as manifest_fd:
        json.dump(manifest, manifest_fd, indent=4)

    # TODO: This should be a template file, or dynamically generated
    describe_file = os.path.join(path, "conf", "describe.xml")
    with open(describe_file, "w") as describe_fd:
        describe_fd.write(
            f"""<?xml version = '1.0' encoding = 'UTF-8'?>
<!-- <!DOCTYPE AdapterKind SYSTEM "describeSchema.xsd"> -->
<AdapterKind key="{adapter_key}" nameKey="1" version="1" xmlns="http://schemas.vmware.com/vcops/schema">
    <CredentialKinds>
    </CredentialKinds>
    <ResourceKinds>
        <ResourceKind key="{adapter_key}_adapter_instance" nameKey="2" type="7">
            <ResourceIdentifier dispOrder="1" key="ID" length="" nameKey="3" required="true" type="string" identType="1" enum="false" default=""></ResourceIdentifier>
        </ResourceKind>
        <ResourceKind key="CPU" nameKey="4"></ResourceKind>
        <ResourceKind key="Disk" nameKey="5"></ResourceKind>
        <ResourceKind key="System" nameKey="6"></ResourceKind>
    </ResourceKinds>
</AdapterKind>""")

    # copy describe.xsd into conf directory
    src = get_absolute_project_directory("tools", "templates", "describeSchema.xsd")
    dest = os.path.join(path, "conf")
    copy(src, dest)

    # create project structure
    executable_directory_path = build_project_structure(path, manifest["name"], language)

    # create Dockerfile
    create_dockerfile(language, path, executable_directory_path)

    # create Commandsfile
    create_commands_file(language, path, executable_directory_path)
    print("")
    print("")
    print("project generation completed")


def create_dockerfile(language: str, root_directory: os.path, executable_directory_path: str):
    print("generating Dockerfile")
    version_file_path = get_absolute_project_directory(constant.VERSION_FILE)
    images = [get_config_value("base_image", config_file=version_file_path)] + \
             get_config_value("secondary_images", config_file=version_file_path)
    version = next(iter(filter(
        lambda image: image["language"].lower() == language,
        images
    )))["version"]

    with open(os.path.join(root_directory, "Dockerfile"), "w") as dockerfile:
        # NOTE: This host is only accessible internally, for future releases we have to provide a public host
        dockerfile.write(
            "# If the harbor repo isn't accessible, the vrops-adapter-open-sdk-server image can be built locally.\n")
        dockerfile.write(
            "# Go to the vrops-python-sdk repo, and run the build_images.py script located at tool/build_images.py\n")
        dockerfile.write(f"FROM harbor-repo.vmware.com/tvs/vrops-adapter-open-sdk-server:{language}-{version}\n")
        dockerfile.write(f"COPY {executable_directory_path} {executable_directory_path}\n")
        dockerfile.write(f"COPY commands.cfg .\n")

        if "python" in language:
            dockerfile.write(f"COPY adapter_requirements.txt .\n")
            dockerfile.write("RUN pip3 install -r adapter_requirements.txt")


def create_commands_file(language: str, path: str, executable_directory_path: str):
    print("generating commands file")
    with open(os.path.join(path, "commands.cfg"), "w") as commands:

        command_and_executable = ""
        if "java" == language:
            command_and_executable = f"/usr/bin/java -cp {executable_directory_path} Collector"
        elif "python" == language:
            command_and_executable = f"/usr/local/bin/python {executable_directory_path}/adapter.py"
        elif "powershell" == language:
            command_and_executable = f"/usr/bin/pwsh {executable_directory_path}/collector.ps1"
        else:
            print(f"ERROR: language {language} is not supported")
            exit(-1)

        commands.write("[Commands]\n")
        commands.write(f"test={command_and_executable} test\n")
        commands.write(f"collect={command_and_executable} collect\n")
        commands.write(f"endpoint_urls={command_and_executable} endpoint_urls\n")


def build_project_structure(path: str, adapter_kind: str, language: str):
    print("generating project structure")
    project_directory = ''  # this is where all the source code will reside

    if language == "python":
        project_directory = "app"
        mkdir(path, project_directory)

        # create template requirements.txt
        requirements_file = os.path.join(path, "adapter_requirements.txt")
        with open(requirements_file, "w") as requirements:
            # Remove the extra-index-url once the vrops-integration library is in the main pypi repository
            requirements.write("--extra-index-url https://testpypi.python.org/pypi\n")
            requirements.write("psutil==5.9.0\n")
            requirements.write("vrops-integration==0.0.12\n")

        # get the path to templates.py
        src = get_absolute_project_directory("tools", "templates", "adapter.py")
        dest = os.path.join(path, project_directory)

        # copy adapter.py into app directory
        copy(src, dest)

        with open(os.path.join(path, project_directory, "constants.py"), "w") as constants:
            constants.write(f'ADAPTER_KIND = "{adapter_kind}"')

    if language == "java":
        # TODO: copy a java class instead of generate it

        mkdir(path, "src")
        java.build_template(path, "src")

        project_directory = "out"
        mkdir(path, project_directory)
        java.compile(os.path.join(path, "src"), os.path.join(path, project_directory, ))

    if language == "powershell":
        # TODO: copy a powershell script  instead of generate it

        project_directory = "scripts"
        mkdir(path, project_directory)
        powershell.build_template(path, project_directory)

    return project_directory


if __name__ == '__main__':
    main()
