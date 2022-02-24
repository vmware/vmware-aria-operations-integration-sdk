import json
import os
import shutil

from shutil import copy
from PyInquirer import style_from_dict, Token, prompt
from PIL import Image, UnidentifiedImageError

import adapter.java as java
import adapter.powershell as powershell


def is_directory_or_not_existing(p: str):
    if not os.path.exists(p):
        return True
    if os.path.isfile(p):
        return 'Path must be a directory.'

    return True


def is_valid_image(p: str):
    try:
        image = Image.open(p, formats=["PNG"])
        return True if image.size == (256, 256) else "Image must be 256X256 pixels"
    except FileNotFoundError:
        return "Could not find image"
    except TypeError:
        return "Image must be in PNG format"
    except UnidentifiedImageError as e:
        return f"{e}"


def main():
    style = style_from_dict({
        Token.QuestionMark: "#E91E63 bold",
        Token.Selected: "#673AB7 bold",
        Token.Instruction: "",
        Token.Answer: "#2196f3 bold",
        Token.Question: "",
    })  # this is the same style used by the build tool

    questions = [
        {
            "type": "input",
            "name": "project_directory",
            "message": "Project directory name (where code for collection, metadata, and content reside):",
            "validate": is_directory_or_not_existing
        },
        {
            'type': 'input',
            'name': 'name',
            'message': 'Display name',
        },
        {
            'type': 'input',
            'name': 'description',
            'message': 'Description',
        },
        {
            'type': 'input',
            'name': 'vendor',
            'message': 'Your company',
        },
        {
            "type": "confirm",
            "name": "eula",
            "message": "Do you have a EULA?"
        },
        {
            'type': 'input',
            'name': 'eula_file',
            'message': 'What is the path to the EULA file?',
            'when': lambda a: a['eula'],
            'validate': lambda file: True if os.path.isfile(file) else 'Path must be a directory.'
        },
        {
            "type": "expand",
            "name": "eula",
            'when': lambda a: not a['eula'],
            "message": "EULA can be added later by setting the 'eula_file' key in 'manifest.txt' and adding the eula "
                       "file to the root project directory.",
            'default': 'k',
            'choices': [
                {'key': 'k', 'name': 'Ok', 'value': 'Ok'}
            ]
        },
        {
            "type": "confirm",
            "name": "icon",
            "message": "Do you have an icon for the management pack?"
        },
        {
            'type': 'input',
            'name': 'icon_file',
            'message': 'What is the path to the icon file?',
            'when': lambda a: a['icon'],
            'validate': is_valid_image
        },
        {
            "type": "expand",
            "name": "eula",
            'when': lambda a: not a['icon'],
            "message": "An icon can be added later by setting the 'pak_icon' key in 'manifest.txt and adding the icon "
                       "file to the root project directory.",
            'default': 'k',
            'choices': [
                {'key': 'k', 'name': 'Ok', 'value': 'Ok'}
            ]
        },
        {
            'type': 'list',
            'name': 'language',
            'message': 'What language would you like to use?',
            'choices': ['Python', 'Java', 'Powershell'],
            'filter': lambda l: l.lower()
        }
        # TODO tell user what that the language is going to be used to create a template Adapter
    ]

    answers = prompt(questions, style=style)

    path = answers["project_directory"]
    name = answers['name']

    # create project_directory
    mkdir(path)

    paths = []
    if os.path.isfile("projects"):
        with open("projects", "r") as projects:
            paths = [project.strip() for project in projects.readlines()]
    if path not in paths:
        with open("projects", "a") as projects:
            projects.write(f"{path}\n")

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
        resources_fd.write(f"DESCRIPTION={answers['description']}\n")
        resources_fd.write("\n")
        resources_fd.write("#The vendor's localized name\n")
        resources_fd.write(f"VENDOR={answers['vendor']}\n")

    if 'eula_file' not in answers:
        eula_file = ""
    else:
        eula_file = answers['eula_file']
        copy(eula_file, path)
        eula_file = os.path.basename(eula_file)

    if 'icon_file' not in answers:
        icon_file = ""
    else:
        icon_file = answers['icon_file']
        copy(icon_file, path)
        icon_file = os.path.basename(icon_file)

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

    # TODO: This should be a template file, or dynamically generated
    describe_file = os.path.join(path, "conf", "describe.xml")
    with open(describe_file, "w") as describe_fd:
        describe_fd.write(
            f"""<?xml version = '1.0' encoding = 'UTF-8'?>
            <!-- <!DOCTYPE AdapterKind SYSTEM "describeSchema.xsd"> -->
            <AdapterKind key="{manifest['name']}" nameKey="1" version="1" xmlns="http://schemas.vmware.com/vcops/schema">
                <CredentialKinds>
                </CredentialKinds>
                <ResourceKinds>
                    <ResourceKind key="{manifest['name']}_adapter_instance" nameKey="2" type="7">
                        <ResourceIdentifier dispOrder="1" key="ID" length="" nameKey="3" required="true" type="string" identType="1" enum="false" default=""></ResourceIdentifier>
                    </ResourceKind>
                </ResourceKinds>
            </AdapterKind>""")

    print("")

    language = answers['language']
    # create project structure
    executable_directory_path = build_project_structure(path, language);

    # create Dockerfile
    create_dockerfile(language, path, executable_directory_path)

    # create Commandsfile
    create_commands_file(language, path, executable_directory_path)
    print("")
    print("project generation completed")


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


def create_dockerfile(language: str, root_directory: os.path, executable_directory_path: str):
    print("generating Dockerfile")
    with open(os.path.join(root_directory, "Dockerfile"), 'w') as dockerfile:
        dockerfile.write(f"FROM vrops-adapter-open-sdk-server:{language}-latest\n")
        dockerfile.write(f"COPY {executable_directory_path} {executable_directory_path}\n")
        dockerfile.write(f"COPY commands.cfg .\n")

        if 'python' in language:
            dockerfile.write(f"COPY adapter_requirements.txt .\n")
            dockerfile.write("RUN pip3 install -r adapter_requirements.txt")


def create_commands_file(language: str, path: str, executable_directory_path: str):
    print("generating commands file")
    with open(os.path.join(path, "commands.cfg"), 'w') as commands:

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
        commands.write("[Version]\n")
        commands.write("major:1\n")
        commands.write("minor:0\n")


def build_project_structure(path: str, language: str):
    print("generating project structure")
    project_directory = ''  # this is where all the source code will reside

    if language == "python":
        project_directory = "app"
        mkdir(path, project_directory)

        # create template requirements.txt
        requirements_file = os.path.join(path, "adapter_requirements.txt")
        with open(requirements_file, "w") as requirements:
            requirements.write("psutil==5.9.0")

        # get the path to adapter.py
        src = os.path.join(os.path.realpath(__file__).split('main.py')[0], 'adapter/adapter.py')
        dest = os.path.join(path, project_directory)

        # copy adapter.py into app directory
        copy(src, dest)

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
