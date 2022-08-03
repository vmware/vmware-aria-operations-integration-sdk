#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import docker

import common.constant as constant
from common import docker_wrapper
from common.config import get_config_value, set_config_value
from common.docker_wrapper import login, init, push_image, BuildError, PushError
from common.filesystem import get_absolute_project_directory
from common.ui import selection_prompt, multiselect_prompt, print_formatted as print


def update_version(update_type: str, current_version: str) -> str:
    semantic_components = list(map(int, current_version.split(".")))

    if update_type == "major":
        semantic_components[0] = semantic_components[0] + 1
        semantic_components[1] = 0
        semantic_components[2] = 0
    elif update_type == "minor":
        semantic_components[1] = semantic_components[1] + 1
        semantic_components[2] = 0
    elif update_type == "patch":
        semantic_components[2] = semantic_components[2] + 1
    else:
        raise ValueError(f"Value not identified: {update_type}")

    return ".".join(map(str, semantic_components))


def should_update_version(language: str, current_version: str) -> str:
    return selection_prompt(
        message=f"Update the version of the {language} image (current version: {current_version})",
        items=[
            ("major", "Major"),
            ("minor", "Minor"),
            ("patch", "Patch"),
            ("no_update", "No Update")
        ])


def get_images_to_build(base_image: dict, secondary_images: [dict]) -> [dict]:
    # Create an array with the base image as the first option
    choices = [(base_image, f"{base_image['language']}", True)]

    # Create choices for all secondary images and add it to the current choices
    choices.extend([(i, f"{i['language']}", False) for i in secondary_images])

    images = multiselect_prompt(
        message="Select one or more docker images to build:",
        items=choices)

    if len(images) == 0:
        print("No images were selected to build. Exiting.")
        exit(1)

    return images


def main():
    client = init()
    version_file_path = get_absolute_project_directory(constant.VERSION_FILE)
    registry_url = get_config_value("registry_url", default="harbor-repo.vmware.com", config_file=version_file_path)
    repo = get_config_value("docker_repo", default="tvs", config_file=version_file_path)

    base_image, secondary_images = get_latest_vrops_container_versions()

    images_to_build = get_images_to_build(base_image, secondary_images)

    for image in images_to_build:
        update = should_update_version(image["language"], image["version"])

        if update != "no_update":
            image["version"] = update_version(update_type=update, current_version=image["version"])

    # Update the versions of the images
    if base_image in images_to_build:
        set_config_value("base_image", base_image, version_file_path)
    if any(i in images_to_build for i in secondary_images):
        set_config_value("secondary_images", secondary_images, version_file_path)

    push_to_registry: bool = selection_prompt(
        message=f"Push images to {registry_url}/{repo}?",
        items=[(True, "Yes"),
               (False, "No")])

    if push_to_registry:
        version_file_path = get_absolute_project_directory(constant.VERSION_FILE)
        registry_url = get_config_value("registry_url", default="harbor-repo.vmware.com", config_file=version_file_path)
        login(registry_url)
        repo = get_config_value("docker_repo", default="tvs", config_file=version_file_path)

    for image in images_to_build:
        try:
            new_image = build_image(
                client=client,
                language=image["language"].lower(),
                version=image["version"],
                path=image["path"]
            )

            if push_to_registry:
                push_image_to_registry(client, new_image, registry_url, repo)
        except BuildError as build_error:
            print(f"Failed to build {image['language']} image")
            print(build_error.message)
            print(build_error.recommendation)


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
    image, _ = docker_wrapper.build_image(client,
                                          path=build_path,
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
        #       See Jira: https://jira.eng.vmware.com/browse/VOPERATION-29771
        reference_tag = f"{registry_tag}/{tag}"
        image.tag(reference_tag)
        try:
            push_image(client, reference_tag)
        except PushError:
            print(f"ERROR: Failed to push {reference_tag}")
        finally:
            print(f"Removing {reference_tag} from local client")
            client.images.remove(reference_tag)


if __name__ == "__main__":
    main()
