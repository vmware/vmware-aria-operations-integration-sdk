#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import os
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import docker
from docker import DockerClient
from docker.models.images import Image

from vmware_aria_operations_integration_sdk import docker_wrapper
from vmware_aria_operations_integration_sdk.config import get_config_value
from vmware_aria_operations_integration_sdk.config import set_config_value
from vmware_aria_operations_integration_sdk.constant import CONTAINER_BASE_NAME
from vmware_aria_operations_integration_sdk.constant import CONTAINER_REGISTRY_HOST
from vmware_aria_operations_integration_sdk.constant import CONTAINER_REGISTRY_PATH
from vmware_aria_operations_integration_sdk.docker_wrapper import BuildError
from vmware_aria_operations_integration_sdk.docker_wrapper import init
from vmware_aria_operations_integration_sdk.docker_wrapper import login
from vmware_aria_operations_integration_sdk.docker_wrapper import push_image
from vmware_aria_operations_integration_sdk.docker_wrapper import PushError
from vmware_aria_operations_integration_sdk.ui import multiselect_prompt
from vmware_aria_operations_integration_sdk.ui import print_formatted as print
from vmware_aria_operations_integration_sdk.ui import selection_prompt

VERSION_FILE = "../vmware_aria_operations_integration_sdk/container_versions.json"


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


def should_update_version(language: str, current_version: str) -> Any:
    return selection_prompt(
        message=f"Update the version of the {language} image (current version: {current_version})",
        items=[
            ("major", "Major"),
            ("minor", "Minor"),
            ("patch", "Patch"),
            ("no_update", "No Update"),
        ],
    )


def get_images_to_build(base_image: dict, secondary_images: List[Dict]) -> List[Dict]:
    # Create an array with the base image as the first option
    # Note: The third element (False) means it's NOT pre-selected by default
    # Users can toggle selections using SPACE bar and confirm with ENTER
    choices = [(base_image, f"{base_image['language']} (base image)", False)]

    # Create choices for all secondary images and add it to the current choices
    # Indicate that secondary images include the base image
    choices.extend([
        (i, f"{i['language']} (includes {base_image['language']} base)", False) 
        for i in secondary_images
    ])

    print("\nUse SPACE to select/deselect images, ENTER to confirm, ↑/↓ to navigate")
    
    images: List[Dict] = multiselect_prompt(  # type: ignore
        message="Select one or more images to build:", items=choices
    )

    if len(images) == 0:
        print("No images were selected to build. Exiting.")
        exit(1)

    # If any secondary image is selected, ensure the base image is also included
    # because secondary images depend on the base image
    has_secondary = any(img in secondary_images for img in images)
    has_base = base_image in images
    
    if has_secondary and not has_base:
        print(f"\nNote: {base_image['language']} base image will be built first (required for selected images)")
        images.insert(0, base_image)
    
    # Ensure base image is built first if it's in the list
    if has_base and images[0] != base_image:
        images.remove(base_image)
        images.insert(0, base_image)

    # Display what will be built
    print(f"\nSelected {len(images)} image(s) to build:")
    for img in images:
        print(f"  - {img['language']}")
    print()

    return images


def main() -> None:
    client = init()
    # Note: This tool is not included in the SDK. It is intended to be run only from the git repository;
    # as such we assume relative paths will work
    registry_url = get_config_value(
        "registry_url",
        default=f"{CONTAINER_REGISTRY_HOST}/{CONTAINER_REGISTRY_PATH}",
        config_file=VERSION_FILE,
    )

    base_image, secondary_images = get_latest_aria_ops_container_versions()

    images_to_build = get_images_to_build(base_image, secondary_images)

    for image in images_to_build:
        update = should_update_version(image["language"], image["version"])

        if update != "no_update":
            image["version"] = update_version(
                update_type=update, current_version=image["version"]
            )

    # Update the versions of the images
    if base_image in images_to_build:
        set_config_value("base_image", base_image, VERSION_FILE)
    if any(i in images_to_build for i in secondary_images):
        set_config_value("secondary_images", secondary_images, VERSION_FILE)

    push_to_registry: bool = selection_prompt(
        message=f"Push images to {registry_url}?", items=[(True, "Yes"), (False, "No")]
    )

    if push_to_registry:
        login(container_registry=registry_url)

    print(f"\n{'='*60}")
    print(f"Building {len(images_to_build)} image(s)...")
    print(f"{'='*60}\n")

    for idx, image in enumerate(images_to_build, 1):
        language = image["language"].lower()
        version = image["version"]

        print(f"\n[{idx}/{len(images_to_build)}] Building {image['language']} image (version {version})...")
        print(f"    Path: {image['path']}")
        print(f"    Language: {language}")
        print(f"{'='*60}\n")

        tags = [
            f"{language}-{version}",
            f"{language}-{version.split('.')[0]}.{version.split('.')[1]}",
            f"{language}-{version.split('.')[0]}",
            f"{language}-latest",
        ]

        try:
            new_image = build_image(
                client=client,
                language=language,
                path=image["path"],
            )

            add_tags(new_image, CONTAINER_BASE_NAME, tags)

            if push_to_registry:
                external_registry_name = f"{registry_url}/{CONTAINER_BASE_NAME}"
                add_tags(new_image, external_registry_name, tags)
                push_image_to_registry(client, external_registry_name, tags)
                remove_tags(client, external_registry_name, tags)
        except BuildError as build_error:
            print(f"Failed to build {image['language']} image")
            print(build_error.message)
            print(build_error.recommendation)


def get_latest_aria_ops_container_versions() -> Tuple[Dict, List[Dict]]:
    # Note: This tool is not included in the SDK. It is intended to be run only from the git repository;
    # as such we assume relative paths will work
    base_image: dict = get_config_value("base_image", config_file=VERSION_FILE)
    secondary_images: List[Dict] = get_config_value(
        "secondary_images", config_file=VERSION_FILE
    )

    # TODO: validate each key, if the key doesn't exist, or doesn't have a value, ask user

    return base_image, secondary_images


def build_image(client: docker.client, language: str, path: str) -> Image:
    # Note: This tool is not included in the SDK. It is intended to be run only from the git repository;
    # as such we assume relative paths will work
    build_path = os.path.join(os.path.realpath("."), path)

    # TODO use Low level API to show user build progress
    image, _ = docker_wrapper.build_image(
        client, path=build_path, tag=CONTAINER_BASE_NAME
    )
    # TODO try pulling/building base image

    return image


def add_tags(image: Image, name: str, tags: List[str]) -> None:
    for tag in tags:
        print(f"tagging '{name}' image with tag: '{tag}'")
        image.tag(name, tag)

    image.reload()  # Update all image attributes


def remove_tags(client: docker.client, image_name: str, tags: List[str]) -> None:
    for tag in tags:
        print(f"removing {image_name}:{tag}")
        client.images.remove(image=f"{image_name}:{tag}")


def push_image_to_registry(
    client: DockerClient, registry_tag: str, tags: List[str]
) -> None:
    for tag in tags:
        try:
            print(f"Pushing to '{registry_tag}:{tag}'...")
            push_image(client, registry_tag, tag)
        except PushError:
            print(f"ERROR: Failed to push {registry_tag}:{tag}")


if __name__ == "__main__":
    main()
