import docker

from common.config import get_config_values, get_config_value
from common.filesystem import get_absolute_project_directory
from PyInquirer import prompt, Token, style_from_dict

style = style_from_dict({
    Token.QuestionMark: "#E91E63 bold",
    Token.Selected: "#673AB7 bold",
    Token.Instruction: "",
    Token.Answer: "#2196f3 bold",
    Token.Question: "",
})  # TODO add style to common lib


def main():
    client = docker.from_env()

    # TODO get current versions
    local_images = client.images.list(name='vrops-adapter-open-sdk-server')  # Get all the images in the repo
    current_python_version, current_java_version, current_powershell_version = get_latest_vrops_container_versions(
        local_images)

    question = [
        {
            'type': 'checkbox',
            'message': 'Which images would you like to build?',
            'name': 'images',
            'choices': [
                {
                    'name': 'Python', # This image should always be built with every new version of the http server
                    'value': 'python:http-server',  # value = [language]:[path]
                    'checked': True
                },
                {
                    'name': 'Java',
                    'value': 'java:java-client'
                },
                {
                    'name': 'PowerShell',
                    'value': 'powershell:powershell-client'
                }
            ],
            'validate': lambda a: 'You must choose at least one image.'
            if len(a) == 0 else True  # Validation doesn't work: https://github.com/CITGuru/PyInquirer/issues/161
        },
        {
            'type': 'confirm',
            'message': "is this a new image (should the image version be updated)?",
            'name': 'update_version',
        },
        {
            'type': 'input',
            'message': f'What is the new base image version (current {current_python_version})',
            'name': 'http_server_version',
            'when': lambda a: a['update_version'] and len(a['images']) > 0 and 'python:http-server' in a['images'],
            'validate': lambda
                a: "Version should be bigger than the current version" if a <= current_python_version else True
        },
        {
            'type': 'input',
            'message': 'What is the Java image version',
            'name': 'java_version',
            'when': lambda a: a['update_version'] and len(a['images']) > 0 and 'java:java-client' in a['images'],
            'validate': lambda
                a: "New version should be bigger than the current version" if a <= current_java_version else True
        },
        {
            'type': 'input',
            'message': 'What is the new PowerShell version',
            'name': 'powershell_version',
            'when': lambda
                a: a['update_version'] and len(a['images']) > 0 and 'powershell:powershell-client' in a['images'],
            'validate': lambda
                a: "New version should be bigger than the current version" if a <= current_powershell_version else True
        }
    ]

    answer = prompt(question, style=style)

    new_images = []

    # TODO: get new versions
    for image in answer['images']:
        # TODO: Prompt user to increment
        new_images.append(build_image(client, image))

    # #TODO ask if the user wants to push the images
    # print("TODO: ask to tag and push images")
    # repo = get_config_value("docker_repo", "tvs")

    # registry_url = login(client)
    #
    # #TODO tag images
    # print("TODO: tag images")
    # print(f"TODO: repo: {repo}")
    #
    # #TODO push images
    # print("TODO: push")
    # print(f"TODO: registry: {registry_url}")


def get_latest_vrops_container_versions(local_images):
    # TODO: parse the images and return each major version
    python_version = '0.3.0'
    java_version = '0.3.0'
    powershell_version = '0.3.0'

    return python_version, java_version, powershell_version


def build_image(client: docker.client, image: str):
    # TODO: Ask to bump version and give a dev option
    language = image.split(':')[0]
    # TODO determine base image version
    # TODO only ask major version for the base image
    version = get_config_value(f"{language}_image_version")
    build_path = get_absolute_project_directory(image.split(':')[1])

    # TODO If image is not base image pass major version as a build parameter
    print(f"building {language} image...")
    image, image_logs = client.images.build(path=build_path, nocache=True, rm=True,
                                            buildargs={"http_server_version": version},
                                            tag=f"vrops-adapter-open-sdk-server:{language}-{version}")

    # TODO ask user if they want to add stable tags
    add_stable_tags(image, language, version)
    image.reload()  # Update all image attributes

    return image


def add_stable_tags(image, language: str, version: str):  # Add type to image
    print(f"image came with this tags{image.tags}")
    tags = [
        f"vrops-adapter-open-sdk-server:{language}-{version.split('.')[0]}",
        f"vrops-adapter-open-sdk-server:{language}-latest"
    ]

    for tag in tags:
        print(f"tagging image with tag {tag}")
        image.tag(tag)


def add_registry_tags(tags: [str], registry_url: str, repo: str):
    pass
    # TODO finish pushing tags logic
    # for tag in tags:
    #     print(f"pushing tag {tag}")
    #     image.tag(tag)
    #     # TODO: This works for Harbor but is probably not generic enough for other registries.
    #     #       See Jira: https://jira.eng.vmware.com/browse/VOPERATION-29771
    #     registry_tag = f"{registry_url}/{repo}/{tag}"
    #     image.tag(registry_tag)


def push_images_to_registry(images):
    pass
    # TODO finish method
    # client.images.push(registry_tag)
    #
    # print("Successfully pushed tags:")
    # for tag in tags:
    #     print(f"    {tag}")
    # print(f"To registry {registry_url}")


def login(docker_client):
    docker_login_config = get_config_values("username", "password", "registry_url",
                                            defaults={
                                                "registry_url": "harbor-repo.vmware.com"})  # TODO passwords shouldn't be stored in this json since we are tracking it in git

    docker_client.login(
        username=docker_login_config["username"],
        password=docker_login_config["password"],
        registry=docker_login_config["registry_url"]
    )

    return docker_login_config["registry_url"]


if __name__ == '__main__':
    main()
