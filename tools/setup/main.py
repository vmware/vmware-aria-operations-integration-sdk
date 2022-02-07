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

    path = input_with_retry("Project directory (where code for collection, metadata, and content reside): ", is_directory_or_not_existing)
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

    supported_languages = ["python","java","powershell"]
    print(f"Supported languages are: {supported_languages}")
    language = input_with_retry("What language would you like to use? ", lambda x: x.lower() in supported_languages).lower()

    # create project structure
    executable_directory_path = build_project_structure(path, language);

    # create Dockerfile
    create_dockerfile(language, path, executable_directory_path)

    # create Commandsfile
    create_commands_file(language ,path, executable_directory_path)


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

def create_dockerfile(language: str, root_directory: os.path: str, executable_directory_path: str):
    with open(os.path.join(root_directory,"Dockerfile"),'w') as dockerfile:
        dockerfile.write(f"FROM vrops-adapter-open-sdk-server:{language}-latest\n")
        dockerfile.write(f"COPY {executable_directory_path} {executable_directory_path}\n")
        dockerfile.write(f"COPY commands.cfg .\n")

def create_commands_file(language: str, path: str, executable_directory_path: str):
    with open(os.path.join(path,"commands.cfg"),'w') as commands:

       command_and_executable = ""
       if("java" == language ):
           command_and_executable = f"/usr/bin/java -cp {executable_directory_path} Collector"
       elif("python" == language):
           command_and_executable = f"/usr/local/bin/python {executable_directory_path}/collector.py"
       elif("powershell" == language):
           command_and_executable = f"/usr/bin/pwsh {executable_directory_path}/collector.ps1"
       else:
           print(f"ERROR: language {language} is not supported")
           exit(-1)

       commands.write("[Commands]\n")
       commands.write(f"test={command_and_executable} test\n")
       commands.write(f"collect={command_and_executable} collect\n")
       commands.write("[Version]\n")
       commands.write("major:0\n")#TODO: where should the version come from  ?
       commands.write("minor:1\n")

def build_project_structure(path: str, language: str):
    project_directory = ''

    if language == "python":
        project_directory = "app"
        mkdir(path, project_directory)
        build_python_template(path, project_directory)

    if language == "java":

        mkdir(path, "src")
        build_java_template(path, "src")

        project_directory =  "out"
        mkdir(path, project_directory)
        compile_java_template(os.path.join(path,"src"), os.path.join(path,project_directory))

    if language == "powershell":
        project_directory = "scripts"
        mkdir(path, project_directory)
        build_powershell_template(path, project_directory)


    return project_directory

def build_java_template(path: str, root_directory: str):
    with open(os.path.join(path, root_directory, "Collector.java"),'w') as collector:
        collector.write(
"""
public class Collector {
    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("No Arguments");
        } else if (args[0].equals("collect")) {
            System.out.println("Java collect");
        } else if (args[0].equals("test")) {
            System.out.println("Java test");
        } else {
            System.out.println("Command "+ args[0] + " not found");
        }
    }
}

"""
        )

def compile_java_template(source_directory: str, output_directory: str):
    # compile class
    os.system(f"javac -d {output_directory} {source_directory}/Collector.java")


def build_powershell_template(path: str, root_directory: str):

    with open(os.path.join(path, root_directory, "collector.ps1"),'w') as collector:
        collector.write(
"""
if ($args.count -eq 0){
	Write-host "No arguments"
}elseif ($args[0] -eq "collect"){
	Write-host "Powershell collect"
}elseif ($args[0] -eq "test"){
	Write-host "Powershell test"
}else{
	Write-host "Command not found"
}

"""
        )


def build_python_template(path: str, root_directory: str):

    with open(os.path.join(path, root_directory, "collector.py"),'w') as collector:
        collector.write(
"""
import sys

def main(argv):
    if len(argv) == 0:
        print("No arguments")
    elif argv[0] in 'collect':
        print("Python collect")
    elif argv[0] in 'test':
        ptint("Python test")
    else:
        print(f"Command {argv[0]} not found")


if __name__ == '__main__':
    main(sys.argv[1:])

"""
        )

if __name__ == '__main__':
    main()
