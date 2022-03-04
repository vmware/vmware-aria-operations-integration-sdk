import docker
import common.constant as constant

from common.config import get_config_values, get_config_value, set_config_value
from common.filesystem import get_absolute_project_directory
from PyInquirer import prompt
from docker import errors


def update_version(update_type: str, current_version: str) -> str:
    semantic_components = list(map(int, current_version.split(".")))

    if update_type in "major":
        semantic_components[0] = semantic_components[0] + 1
        semantic_components[1] = 0
        semantic_components[2] = 0
    elif update_type in "minor":
        semantic_components[1] = semantic_components[1] + 1
        semantic_components[2] = 0
    elif update_type in "patch":
        semantic_components[2] = semantic_components[2] + 1
    else:
        raise ValueError(f"Value not identified: {update_type}")

    return ".".join(map(str, semantic_components))


def should_update_version(language: str, current_version: str, name: str) -> dict:
    question = {
        "type": "expand",
        "message": f"Update the version of the {language} image (current version:"
                   f" {current_version}) (press h for help)",
        "name": name,
        "choices": [
            {
                "key": "i",
                "name": "minor",
                "value": "minor"
            },
            {
                "key": "p",
                "name": "patch",
                "value": "patch"
            },
            {
                "key": "n",
                "name": "no",
                "value": "no_update"
            },
        ],
        "filter": lambda val: (val, current_version if val == "no_update" else
        update_version(val, current_version))
        # Update the version and keep the type of update for validation
    }

    if language == "Python":
        choices = question.get("choices")
        choices.insert(0, {"key": "m", "name": "major", "value": "major"})
        question.update({"choices": choices})

    return prompt(question, style=constant.PY_INQUIRER_STYLE)


def main():
    client = docker.from_env()

    current_python_version, current_java_version, current_powershell_version = get_latest_vrops_container_versions()

    answers = prompt({
        "type": "checkbox",
        "message": "Select one or more docker images to build: ",
        "name": "images",
        "choices": [
            {
                "name": "Python",  # This image should always be built with every new version of the http server
                "value": ("python", "http-server"),  # Tuple = (language, path)
                "checked": True
            },
            {
                "name": "Java",
                "value": ("java", "java-client")
            },
            {
                "name": "PowerShell",
                "value": ("powershell", "powershell-client")
            }
        ],
        "validate": lambda a: "You must choose at least one image." if len(a) == 0 else True
        # Validation doesn't work: https://github.com/CITGuru/PyInquirer/issues/161
    }, style=constant.PY_INQUIRER_STYLE)

    if len(answers[
               'images']) == 0:  # TODO remove this logic whenever validation for PyInquirer starts working again
        print("You must choose at least one image.")
        exit(1)

    if ("python", "http-server") in answers["images"]:
        answers.update(should_update_version("Python", current_python_version, "http_server_version"))
    if ("java", "java-client") in answers['images'] and (
            "http_server_version" not in answers or (answers["http_server_version"][0] != "major")):
        answers.update(should_update_version("Java", current_java_version, "java_version"))
    if ("powershell", "powershell-client") in answers['images'] and (
            "http_server_version" not in answers or (answers["http_server_version"][0] != "major")):
        answers.update(should_update_version("PowerShell", current_powershell_version, "powershell_version"))

    # Images Should only be pushed if they are new. Old images should already be pushed
    if ("http_server_version" in answers and answers["http_server_version"][0] != "no_update") or \
            ("java_version" in answers and answers["java_version"][0] != "no_update") or \
            ("powershell_version" in answers and answers["powershell_version"][0] != "no_update"):
        answers.update(prompt({
            "type": "confirm",
            "message": f"Push new images?",
            "name": "push_to_registry"
        }, style=constant.PY_INQUIRER_STYLE))
    else:
        answers.update({"push_to_registry": False})

    registry_url = login(client) if answers["push_to_registry"] else False
    repo = get_config_value("docker_repo", "tvs") if answers["push_to_registry"] else False

    # If the http server changed, then all image versions should be updated regardless of them being built
    if "http_server_version" in answers and answers["http_server_version"][0] == "major":
        new_version = answers["http_server_version"][1]
        set_config_value("python_image_version", new_version, constant.VERSION_FILE)
        set_config_value("java_image_version", new_version, constant.VERSION_FILE)
        set_config_value("powershell_image_version", new_version, constant.VERSION_FILE)
    else:
        if "http_server_version" in answers:
            set_config_value("python_image_version", answers["http_server_version"][1], constant.VERSION_FILE)
        if "java_version" in answers:
            set_config_value("java_image_version", answers["java_version"][1], constant.VERSION_FILE)
        if "powershell_version" in answers:
            set_config_value("powershell_image_version", answers["powershell_version"][1], constant.VERSION_FILE)

    new_images = []  # track new images to in order to push them

    for image in answers["images"]:
        new_images.append(build_image(client, image))

    if answers['push_to_registry']:
        push_images_to_registry(client, new_images, registry_url, repo)


def get_latest_vrops_container_versions():
    python_version = get_config_value("python_image_version", config_file=constant.VERSION_FILE)
    java_version = get_config_value("java_image_version", config_file=constant.VERSION_FILE)
    powershell_version = get_config_value("powershell_image_version", config_file=constant.VERSION_FILE)

    return python_version, java_version, powershell_version


def build_image(client: docker.client, image: str):
    language = image[0]
    version = get_config_value(f"{language}_image_version", config_file=constant.VERSION_FILE)
    build_path = get_absolute_project_directory(image[1])

    # TODO use Low level API to show user build progress
    try:
        print(f"building {language} image:vrops-adapter-open-sdk-server:{language}-{version}...")
        image, _ = client.images.build(path=build_path, nocache=True, rm=True,
                                       buildargs={"http_server_version": version.split(".")[0]},
                                       tag=f"vrops-adapter-open-sdk-server:{language}-{version}")

    except errors.BuildError as e:
        base_image_tag = f"vrops-adapter-open-sdk-server:python-{version.split('.')[0]}"
        if len(client.images.list(base_image_tag)) == 0:
            print(f"Pull {base_image_tag} before building images for {language}")
            exit(1)
        else:  # TODO Improve error handling
            raise e

    add_stable_tags(image, language, version)
    image.reload()  # Update all image attributes

    return image


def add_stable_tags(image, language: str, version: str):
    tags = [
        f"vrops-adapter-open-sdk-server:{language}-{version.split('.')[0]}",
        f"vrops-adapter-open-sdk-server:{language}-latest"
    ]

    for tag in tags:
        print(f"tagging {language} image with tag: {tag}")
        image.tag(tag)


def push_images_to_registry(client, images, registry_url: str, repo):
    registry_tag = f"{registry_url}/{repo}"
    print(f"pushing image{'s' if len(images) > 1 else ''} to {registry_tag}")
    for image in images:
        for tag in image.tags:
            # TODO: This works for Harbor but is probably not generic enough for other registries.
            #       See Jira: https://jira.eng.vmware.com/browse/VOPERATION-29771
            reference_tag = f"{registry_tag}/{tag}"
            image.tag(reference_tag)
            for line in client.images.push(reference_tag, stream=True, decode=True):
                print(line)

            print(f"removing {reference_tag} from local client")
            client.images.remove(reference_tag)


def login(docker_client):
    docker_login_config = get_config_values("username", "password", "registry_url",
                                            defaults={
                                                "registry_url": "harbor-repo.vmware.com"})

    docker_client.login(
        username=docker_login_config["username"],
        password=docker_login_config["password"],
        registry=docker_login_config["registry_url"]
    )

    return docker_login_config["registry_url"]


if __name__ == "__main__":
    main()
