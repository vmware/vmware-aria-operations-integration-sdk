import docker
import PyInquirer

from common.config import get_config_values, get_config_value
from common.filesystem import get_absolute_project_directory
from PyInquirer import prompt, Separator, Token, style_from_dict

style = style_from_dict({
    Token.QuestionMark: "#E91E63 bold",
    Token.Selected: "#673AB7 bold",
    Token.Instruction: "",
    Token.Answer: "#2196f3 bold",
    Token.Question: "",
})  # TODO add style to common lib


def main():
    question = [
        {
            'type': 'checkbox',
            'message': 'Which images would you like to build?',
            'name': 'images',
            'choices': [
                {
                    'name': 'Python',
                    'value': 'python:http-server',# value = [language]:[path]
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
        }
    ]
    answer = prompt(question, style=style)

    client = docker.from_env()

    for image in answer['images']:
        # TODO: Prompt user to increment
        build_image(client, image)  # TODO build local image

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


def build_image(client: docker.client, image: str):
    # TODO: Ask to bump version and give a dev option
    language = image.split(':')[0]
    version = get_config_value(f"{language}_image_version")
    build_path = get_absolute_project_directory(image.split(':')[1])
    print(f"build path: {build_path}")
    image, image_logs = client.images.build(path=build_path, nocache=True, rm=True,
                                            tag=f"vrops-adapter-open-sdk-server:{language}-{version}")
    print(f"logs for {image}:{image_logs}")


def tag_image(image, version):
    tags = [
        f"vrops-adapter-open-sdk-server:python-{version}",
        f"vrops-adapter-open-sdk-server:python-{version.split('.')[0]}",
        f"vrops-adapter-open-sdk-server:python-latest"
    ]

    for tag in tags:
        print(f"pushing tag {tag}")
        image.tag(tag)
        # TODO: This works for Harbor but is probably not generic enough for other registries.
        #       See Jira: https://jira.eng.vmware.com/browse/VOPERATION-29771
        registry_tag = f"{registry_url}/{repo}/{tag}"
        image.tag(registry_tag)


def push_tags(client, registry_tag):
    client.images.push(registry_tag)

    print("Successfully pushed tags:")
    for tag in tags:
        print(f"    {tag}")
    print(f"To registry {registry_url}")


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
