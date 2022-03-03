import docker

from common.config import get_config_values, get_config_value, set_config_value
from common.filesystem import get_absolute_project_directory
from PyInquirer import prompt, Token, style_from_dict

style = style_from_dict({
    Token.QuestionMark: "#E91E63 bold",
    Token.Selected: "#673AB7 bold",
    Token.Instruction: "",
    Token.Answer: "#2196f3 bold",
    Token.Question: "",
})  # TODO add style to common lib


def update_version(update_type: str, current_version: str):
    semantic_components = list(map(int, current_version.split('.')))

    if update_type in 'major':
        semantic_components[0] = semantic_components[0] + 1
        semantic_components[1] = 0
        semantic_components[2] = 0
    elif update_type in 'minor':
        semantic_components[1] = semantic_components[1] + 1
        semantic_components[2] = 0
    elif update_type in 'patch':
        semantic_components[2] = semantic_components[2] + 1
    else:
        raise ValueError("Value not identified")

    return ".".join(map(str, semantic_components))


def main():
    client = docker.from_env()

    current_python_version, current_java_version, current_powershell_version = get_latest_vrops_container_versions()

    question = [
        {
            'type': 'checkbox',
            'message': 'Select one or more docker images to build: ',
            'name': 'images',
            'choices': [
                {
                    'name': 'Python',  # This image should always be built with every new version of the http server
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
            'message': f"Is there a new version of the HTTP Server? (current version: {current_python_version})",
            'name': 'update_http_server_version',
            'when': lambda a: len(a['images']) > 0 and 'python:http-server' in a['images']
        },
        {
            'type': 'expand',
            'message': "What type of version update is this? (press h for help)",
            'name': 'http_server_version',
            'when': lambda a: 'update_http_server_version' in a and a['update_http_server_version'],
            'choices': [
                {
                    'key': 'm',
                    'name': 'major',
                    'value': 'major'
                },
                {
                    'key': 'i',
                    'name': 'minor',
                    'value': 'minor'
                },
                {
                    'key': 'p',
                    'name': 'patch',
                    'value': 'patch'
                },
            ],
            'filter': lambda val: f"{val}:{update_version(val, current_python_version)}"
            # Update the python version and keep the type of update for validation"
        },
        {
            'type': 'confirm',
            'message': f"Update Java Image version? (current version: {current_java_version})",
            'name': 'update_java_image_version',
            'when': lambda
                a: len(a['images']) >= 0 and
                   'java:java-client' in a['images'] and
                   ('http_server_version' not in a or
                   ('http_server_version' in a and 'major' not in a['http_server_version']))
        },
        {
            'type': 'expand',
            'message': "What type of version update is this? (press h for help)",
            'when': lambda a: 'update_java_image_version' in a and a['update_java_image_version'],
            'name': 'java_version',
            'choices': [  # All images major version are based of the HTTP servers major version
                {
                    'key': 'i',
                    'name': 'minor',
                    'value': 'minor'
                },
                {
                    'key': 'p',
                    'name': 'patch',
                    'value': 'patch'
                },
            ],
            'filter': lambda val: update_version(val, current_java_version)
        },
        {
            'type': 'confirm',
            'message': f"Update PowerShell Image version? (current version: {current_powershell_version})",
            'name': 'update_powershell_image_version',
            'when': lambda
                a: len(a['images']) >= 0 and
                   'powershell:powershell-client' in a['images'] and
                   ('http_server_version' not in a or
                   ('http_server_version' in a and 'major' not in a['http_server_version']))
        },
        {
            'type': 'expand',
            'message': "What type of version update is this? (press h for help)",
            'when': lambda a: 'update_powershell_image_version' in a and a['update_powershell_image_version'],
            'name': 'powershell_version',
            'choices': [
                {
                    'key': 'i',
                    'name': 'minor',
                    'value': 'minor'
                },
                {
                    'key': 'p',
                    'name': 'patch',
                    'value': 'patch'
                },
            ],
            'filter': lambda val: update_version(val, current_powershell_version)
        },
        {
            'type': 'confirm',
            'message': f"Would you like to update stable tags",
            'name': 'update_stable_tags',
            'when': lambda
                a: len(a['images']) >= 0 and
                   ('update_powershell_image_version' in a or
                    'update_java_image_version' in a or
                    'update_http_server_version' in a)

        },
        {
            'type': 'confirm',
            'message': f"Would you like to push new images?",
            'name': 'push_to_registry',
            'when': lambda a: 'update_stable_tags' in a and a['update_stable_tags']
        },
    ]

    answers = prompt(question, style=style)

    # If the user wants to push images we might need to ask question, so it's better to ask them right away
    registry_url = login(client) if 'push_to_registry' in answers and answers['push_to_registry'] else False
    repo = get_config_value("docker_repo", "tvs") if 'push_to_registry'in answers and answers['push_to_registry'] else False

    # If the http server changed, then all image versions should be updated regardless of them being built
    if 'http_server_version' in answers and 'major' in answers['http_server_version']:
        new_version = answers['http_server_version'].strip('major:')
        set_config_value('python_image_version', new_version)
        set_config_value('java_image_version', new_version)
        set_config_value('powershell_image_version', new_version)
    else:
        if 'http_server_version' in answers:
            set_config_value('python_image_version', answers['http_server_version'].split(':')[1])
        if 'java_version' in answers:
            set_config_value('java_image_version', answers['java_version'])
        if 'powershell_version' in answers:
            set_config_value('powershell_image_version', answers['powershell_version'])

    new_images = []  # track new images to in order to push them

    should_update_stable_tags = 'update_stable_tags' in answers and answers['update_stable_tags']
    for image in answers['images']:
        new_images.append(build_image(client, image, should_update_stable_tags))

    push_images_to_registry(client, new_images, registry_url, repo)


def get_latest_vrops_container_versions():
    python_version = get_config_value("python_image_version")
    java_version = get_config_value("java_image_version")
    powershell_version = get_config_value("powershell_image_version")

    return python_version, java_version, powershell_version


def build_image(client: docker.client, image: str, stable_tags: bool):
    language = image.split(':')[0]
    version = get_config_value(f"{language}_image_version")
    build_path = get_absolute_project_directory(image.split(':')[1])

    print(f"building {language} image...")
    # TODO use Low level API to show user build progress
    image, image_logs = client.images.build(path=build_path, nocache=True, rm=True,
                                            buildargs={"http_server_version": version},
                                            tag=f"vrops-adapter-open-sdk-server:{language}-{version}")

    if stable_tags:
        add_stable_tags(image, language, version)
        image.reload()  # Update all image attributes

    return image


def add_stable_tags(image, language: str, version: str):  # Add type to image
    tags = [
        f"vrops-adapter-open-sdk-server:{language}-{version.split('.')[0]}",
        f"vrops-adapter-open-sdk-server:{language}-latest"
    ]

    for tag in tags:
        print(f"tagging image with tag: {tag}")
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


if __name__ == '__main__':
    main()
