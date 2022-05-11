import docker
import common.constant as constant
import common.style as style

from common.filesystem import get_absolute_project_directory
from common.config import get_config_values, get_config_value, set_config_value
from common.docker_wrapper import login, init

from PyInquirer import prompt


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


def should_update_version(language: str, current_version: str) -> str:
    return prompt({
        "type": "list",
        "message": f"Update the version of the {language} image (current version:"
                   f" {current_version})",
        "name": "update",
        "choices": [
            {
                "name": "major",
                "value": "major"
            },
            {
                "name": "minor",
                "value": "minor"
            },
            {
                "name": "patch",
                "value": "patch"
            },
            {
                "name": "no update",
                "value": "no_update"
            },
        ]
    }, style=style.vrops_sdk_prompt_style)["update"]


def get_images_to_build(base_image: dict, secondary_images: [dict]) -> [dict]:
    # Create an array with the base image as the first option
    choices = [{
        "name": f"{base_image['language']}",
        "value": base_image,
        "checked": True
    }]

    # Create choices for all secondary images and add it to the current choices
    choices.extend([{"name": f"{i['language']}", "value": i} for i in secondary_images])

    answer = prompt({
        "type": "checkbox",
        "message": "Select one or more docker images to build: ",
        "name": "images",
        "choices": choices,
        "validate": lambda a: "You must choose at least one image." if len(a) == 0 else True
        # Validation doesn't work: https://github.com/CITGuru/PyInquirer/issues/161
    }, style=style.vrops_sdk_prompt_style)

    if len(answer[
               'images']) == 0:  # TODO remove this logic whenever validation for PyInquirer starts working again
        print("No images were selected to build. Exiting.")
        exit(1)

    return answer['images']


def main():
    client = init()
    registry_url = get_config_value("registry_url", default="harbor-repo.vmware.com")
    repo = get_config_value("docker_repo", "tvs")

    base_image, secondary_images = get_latest_vrops_container_versions()

    images_to_build = get_images_to_build(base_image, secondary_images)

    for image in images_to_build:
        update = should_update_version(image["language"], image["version"])

        if update != "no_update":
            image["version"] = update_version(update_type=update, current_version=image["version"])

    # Update the versions of the images
    if base_image in images_to_build:
        set_config_value("base_image", base_image, constant.VERSION_FILE)
    if any(i in images_to_build for i in secondary_images):
        set_config_value("secondary_images", secondary_images, constant.VERSION_FILE)

    push_to_registry: bool = prompt({
        "type": "confirm",
        "message": f"Push images to {registry_url}/{repo}?",
        "name": "push_to_registry"  # TODO add registry and repo
    }, style=style.vrops_sdk_prompt_style)["push_to_registry"]

    if push_to_registry:
        registry_url = login()
        repo = get_config_value("docker_repo", "tvs")

    for image in images_to_build:
        new_image = build_image(client=client, language=image["language"].lower(), version=image["version"], path=image["path"])

        if push_to_registry:
            push_image_to_registry(client, new_image, registry_url, repo)


def get_latest_vrops_container_versions() -> (dict, [dict]):
    version_file_path = get_absolute_project_directory(constant.VERSION_FILE)
    base_image: dict = get_config_value("base_image", config_file=version_file_path)
    secondary_images: [dict] = get_config_value("secondary_images", config_file=version_file_path)

    # TODO: validate each key, if the key doesn't exist, or doesn't have a value, ask user

    return base_image, secondary_images


def build_image(client: docker.client, language: str, version: str, path: str):
    build_path = get_absolute_project_directory(path)

    # TODO use Low level API to show user build progress
    print(f"building {language} image:vrops-adapter-open-sdk-server:{language}-{version}...")
    image, _ = client.images.build(path=build_path,
                                   nocache=True,
                                   rm=True,
                                   tag=f"vrops-adapter-open-sdk-server:{language}-{version}"
                                   )

    # TODO try pulling/building base image

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


def push_image_to_registry(client, image, registry_url: str, repo: str):
    registry_tag = f"{registry_url}/{repo}"
    print(f"pushing image to {registry_tag}")
    for tag in image.tags:
        # TODO: This works for Harbor but is probably not generic enough for other registries.
        #       See Jira: https://jira.eng.vmware.com/browse/VOPERATION-29771
        reference_tag = f"{registry_tag}/{tag}"
        image.tag(reference_tag)
        for line in client.images.push(reference_tag, stream=True, decode=True):
            print(line)

        print(f"removing {reference_tag} from local client")
        client.images.remove(reference_tag)

if __name__ == "__main__":
    main()
