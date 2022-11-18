#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import json
import os.path

from vmware_aria_operations_integration_sdk import docker_wrapper


def combine_swagger_files(base, extra):
    with open(base, "r") as base_file:
        base_json = json.load(base_file)

    with open(extra, "r") as extra_file:
        extra_json = json.load(extra_file)

    for attribute in extra_json["paths"]:
        base_json["paths"][attribute] = extra_json["paths"][attribute]
    for attribute in extra_json["components"]["schemas"]:
        base_json["components"]["schemas"][attribute] = extra_json["components"]["schemas"][attribute]

    return base_json


def main():
    combined = combine_swagger_files(
        os.path.join("..", "vmware_aria_operations_integration_sdk", "api", "vmware-aria-operations-collector-fwk2.json"),
        os.path.join("..", "vmware_aria_operations_integration_sdk", "api", "integration-sdk-definition-endpoint.json"))
    with open("combined.json", "w") as combined_file:
        json.dump(combined, combined_file, indent=3)

    docker_client = docker_wrapper.init()
    image = docker_client.images.pull("swaggerapi/swagger-codegen-cli-v3")
    docker_client.containers.run(image.id, ["generate", "-i", "local/combined.json", "-l", "python-flask", "-o", "local/base-python-adapter"], remove=True, volumes={f"{os.getcwd()}": {"bind": "/local", "mode": "rw"}})


if __name__ == "__main__":
    main()
