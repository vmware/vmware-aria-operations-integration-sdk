import json
import logging
import os
import traceback
from shutil import copy

from git import Repo
from prompt_toolkit import prompt

import common.constant as constant
import templates.java as java
import templates.powershell as powershell
from common.config import get_config_value
from common.filesystem import get_absolute_project_directory, get_root_directory, mkdir, rmdir
from common.project import Project, record_project
from common.ui import print_formatted as print, path_prompt
from common.ui import selection_prompt
from common.validators import NewProjectDirectoryValidator, NotEmptyValidator, AdapterKeyValidator, EulaValidator, \
    ImageValidator

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = logging.StreamHandler()
logger.addHandler(consoleHandler)


def create_manifest_localization_file(path, name, vendor, description):
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


def create_eula_file(path, eula_file):
    if not eula_file:
        eula_file = "eula.txt"
        with open(os.path.join(path, eula_file), "w") as eula_fd:
            # Note: vROps requires a EULA file, and it must not be blank.
            eula_fd.write("There is no EULA associated with this Management Pack.")
    else:
        copy(eula_file, path)
        eula_file = os.path.basename(eula_file)

    return eula_file


def create_icon_file(path, icon_file):
    if not icon_file:
        icon_file = ""
    else:
        copy(icon_file, path)
        icon_file = os.path.basename(icon_file)

    return icon_file


def create_manifest_file(path, adapter_key, eula_file, icon_file):
    manifest_file = os.path.join(path, "manifest.txt")
    manifest = {
        "display_name": "DISPLAY_NAME",
        "name": adapter_key,
        "description": "DESCRIPTION",
        "version": "1.0.0",
        "vcops_minimum_version": "8.7.2",
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

    return manifest


def create_describe(path, adapter_key, name):
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
        <ResourceKind key="CPU" nameKey="4">
            <ResourceAttribute key="user_time" nameKey="5" dataType="float" unit="seconds"/>
            <ResourceAttribute key="nice_time" nameKey="6" dataType="float" keyAttribute="true" unit="seconds"/>
            <ResourceAttribute key="system_time" nameKey="7" dataType="float" unit="seconds"/>
            <ResourceAttribute key="idle_time" nameKey="8" dataType="float" unit="seconds"/>
        </ResourceKind>
        <ResourceKind key="Disk" nameKey="9">
            <ResourceAttribute key="total_space" nameKey="10" dataType="float" unit="bytes"/>
            <ResourceAttribute key="used_space" nameKey="11" dataType="float" unit="bytes"/>
            <ResourceAttribute key="free_space" nameKey="12" dataType="float" unit="bytes"/>
            <ResourceAttribute key="percent_used_space" nameKey = "13" dataType="float" keyAttribute="true" unit="%"/>
        </ResourceKind>
        <ResourceKind key="System" nameKey="13">
        </ResourceKind>
    </ResourceKinds>
</AdapterKind>""")
    describe_resources_file = os.path.join(path, "conf", "resources", "resources.properties")
    with open(describe_resources_file, "w") as describe_resources_fd:
        describe_resources_fd.write("version=1\n")
        describe_resources_fd.write(f"1={name}\n")
        describe_resources_fd.write(f"2={name} Adapter Instance\n")
        describe_resources_fd.write("3=Identifier\n")
        describe_resources_fd.write("4=CPU\n")
        describe_resources_fd.write("5=User Time\n")
        describe_resources_fd.write("6=Nice Time\n")
        describe_resources_fd.write("7=System Time\n")
        describe_resources_fd.write("8=Idle Time\n")
        describe_resources_fd.write("9=Disk\n")
        describe_resources_fd.write("10=Total Space\n")
        describe_resources_fd.write("11=Used Space\n")
        describe_resources_fd.write("12=Free Space\n")
        describe_resources_fd.write("13=Disk Utilization\n")
        describe_resources_fd.write("14=System\n")


def build_content_directory(path):
    content_dir = mkdir(path, "content")
    mkdir(content_dir, "policies")
    mkdir(content_dir, "traversalspecs")
    mkdir(content_dir, "resources")
    mkdir(content_dir, "customgroups")
    mkdir(content_dir, "reports")
    mkdir(content_dir, "recommendations")
    mkdir(content_dir, "dashboards")

    files_dir = mkdir(content_dir, "files")
    mkdir(files_dir, "topowidget")
    mkdir(files_dir, "txtwidget")
    mkdir(files_dir, "solutionconfig")
    mkdir(files_dir, "reskndmetric")

    mkdir(content_dir, "alertdefs")
    mkdir(content_dir, "supermetrics")
    mkdir(content_dir, "symptomdefs")

    return content_dir


def build_project(path, name, adapter_key, description, vendor, eula_file, icon_file, language):
    mkdir(path)

    project = Project(path)
    record_project(project.__dict__)

    build_content_directory(path)
    conf_dir = mkdir(path, "conf")
    conf_resources_dir = mkdir(path, "conf", "resources")

    create_manifest_localization_file(path, name, vendor, description)
    eula_file = create_eula_file(path, eula_file)
    icon_file = create_icon_file(path, icon_file)
    manifest = create_manifest_file(path, adapter_key, eula_file, icon_file)
    create_describe(path, adapter_key, name)

    # copy describe.xsd into conf directory
    src = get_absolute_project_directory("tools", "templates", "describeSchema.xsd")
    dest = os.path.join(path, "conf")
    copy(src, dest)

    # create project structure
    executable_directory_path = build_project_structure(path, manifest["name"], language)

    # create Dockerfile
    create_dockerfile(language, path, executable_directory_path)

    # create Commands File
    create_commands_file(language, path, executable_directory_path)

    # initialize new project as a git repository
    repo = Repo.init(path)
    git_ignore = os.path.join(path, ".gitignore")
    with open(git_ignore, "w") as git_ignore_fd:
        git_ignore_fd.write("\n")
    repo.git.add(all=True)
    repo.index.commit("Initial commit.")
    # TODO: Prompt to create remote, once we know what the default remote should be.
    # remote = repo.create_remote("origin", url="https://gitlab.vmware.com/[...]")
    # remote.push(refspec='main:main')


def main():
    path = ""
    try:
        get_root_directory()

        path = path_prompt(
            "Enter a path for the project directory where adapter code, metadata, and content will reside. \n" +
            "If the directory doesn't already exist, it will be created. \nPath: ",
            validator=NewProjectDirectoryValidator("Path"))

        name = prompt("Management pack display name: ", validator=NotEmptyValidator("Display name"))
        adapter_key = prompt("Management pack adapter key: ",
                             validator=AdapterKeyValidator("Adapter key"),
                             default=AdapterKeyValidator.default(name))
        description = prompt("Management pack description: ", validator=NotEmptyValidator("Description"))
        vendor = prompt("Management pack vendor: ", validator=NotEmptyValidator("Vendor"))
        eula_file = path_prompt("Enter a path to a EULA text file, or leave blank for no EULA: ",
                                validator=EulaValidator())

        if eula_file == "":
            print("A EULA can be added later by editing the default 'eula.txt' file.")
        icon_file = path_prompt("Enter a path to the management pack icon file, or leave blank for no icon: ",
                                validator=ImageValidator())
        if icon_file == "":
            print("An icon can be added later by setting the 'pak_icon' key in 'manifest.txt' to the icon file "
                  "name and adding the icon file to the root project directory.")

        language = selection_prompt("Select a language for the adapter.",
                                    items=[("python", "Python"),
                                           ("java", "Java", "Unavailable for beta release"),
                                           ("powershell", "PowerShell", "Unavailable for beta release")])
        # create project_directory
        build_project(path, name, adapter_key, description, vendor, eula_file, icon_file, language)
        print("")
        print("")
        print("project generation completed")
    except (KeyboardInterrupt, Exception) as error:
        if type(error) is KeyboardInterrupt:
            logger.info("Init cancelled by user")
        else:
            print("Unexpected error")
            logger.error(error)
            traceback.print_tb(error.__traceback__)
        # In both cases, we want to clean up afterwards
        if os.path.exists(path):
            logger.debug("Deleting generated artifacts")
            rmdir(path)


def create_dockerfile(language: str, root_directory: os.path, executable_directory_path: str):
    logger.info("generating Dockerfile")
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
            "# Go to the vrops-integration-sdk repo, and run the build_images.py script located at tool/build_images.py\n")
        dockerfile.write(f"FROM harbor-repo.vmware.com/tvs/vrops-adapter-open-sdk-server:{language}-{version}\n")
        dockerfile.write(f"COPY {executable_directory_path} {executable_directory_path}\n")
        dockerfile.write(f"COPY commands.cfg .\n")

        if "python" in language:
            dockerfile.write(f"COPY adapter_requirements.txt .\n")
            dockerfile.write("RUN pip3 install -r adapter_requirements.txt --upgrade")


def create_commands_file(language: str, path: str, executable_directory_path: str):
    logger.info("generating commands file")
    with open(os.path.join(path, "commands.cfg"), "w") as commands:

        command_and_executable = ""
        if "java" == language:
            command_and_executable = f"/usr/bin/java -cp {executable_directory_path} Collector"
        elif "python" == language:
            command_and_executable = f"/usr/local/bin/python {executable_directory_path}/adapter.py"
        elif "powershell" == language:
            command_and_executable = f"/usr/bin/pwsh {executable_directory_path}/collector.ps1"
        else:
            logger.error(f"language {language} is not supported")
            exit(1)

        commands.write("[Commands]\n")
        commands.write(f"test={command_and_executable} test\n")
        commands.write(f"collect={command_and_executable} collect\n")
        commands.write(f"endpoint_urls={command_and_executable} endpoint_urls\n")


def build_project_structure(path: str, adapter_kind: str, language: str):
    logger.info("generating project structure")
    project_directory = ''  # this is where all the source code will reside

    if language == "python":
        project_directory = "app"
        mkdir(path, project_directory)

        # create template requirements.txt
        requirements_file = os.path.join(path, "adapter_requirements.txt")
        with open(requirements_file, "w") as requirements:
            requirements.write("# Remove the following line once the vrops-integration library is in the main pypi"
                               " repository.\n")
            requirements.write("--extra-index-url https://testpypi.python.org/pypi\n")
            requirements.write("psutil==5.9.0\n")
            requirements.write("vrops-integration==0.0.*\n")

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
