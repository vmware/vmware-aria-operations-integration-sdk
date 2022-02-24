__author__ = 'VMware, Inc.'
__copyright__ = 'Copyright 2022 VMware, Inc. All rights reserved.'

import argparse
import json
import os
import time
import xml.etree.ElementTree as ET
from pprint import pprint

import docker
import requests
import urllib3
from PyInquirer import prompt
from flask import json

from common.project import get_project, Connection, record_project
from common.style import vrops_sdk_prompt_style

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test(arguments):
    print("Running test connection")
    pprint(arguments)

    project = get_project(arguments)
    connection = get_connection(project)

    docker_client = docker.client.from_env()
    image = create_container_image(docker_client, project["path"])
    container = run_image(docker_client, image)

    try:
        post_test(project, connection)
    finally:
        stop_container(container)


def collections(arguments):
    print("Running collection")
    pprint(arguments)

    project = get_project(arguments)
    connection = get_connection(project)

    docker_client = docker.client.from_env()
    image = create_container_image(docker_client, project["path"])
    container = run_image(docker_client, image)

    try:
        post_collect(project, connection)
    finally:
        input("test")
        stop_container(container)


# REST calls ***************

def post_collect(project, connection):
    response = requests.post(
        "http://localhost:8080/collect",
        json=get_request_body(project, connection),
        headers={"Accept": "application/json"})
    print('Response body is : ' + response.text)
    # TODO: Validate response


def post_test(project, connection):
    response = requests.post(
        "http://localhost:8080/test",
        json=get_request_body(project, connection),
        headers={"Accept": "application/json"})
    print('Response body is : ' + response.text)
    # TODO: Validate response


def get_version():
    response = requests.get(
        "http://localhost:8080/version",
        headers={"Accept": "application/json"})
    print('Response body is : ' + response.text)


# Docker helpers ***************

def create_container_image(client, build_path):
    with open(os.path.join(build_path, "manifest.txt")) as manifest_file:
        manifest = json.load(manifest_file)

    docker_image_tag = manifest["name"].lower() + ":" + manifest["version"] + "_" + str(time.time())
    client.images.build(path=build_path, nocache=True, rm=True, tag=docker_image_tag)
    return docker_image_tag


def run_image(client, image):
    return client.containers.run(image, detach=True, ports={"8080/tcp": 8080})


def stop_container(container):
    container.kill()


# TODO: Can we use this to validate the returned json?
# def create_client():
#     logging.getLogger('connexion.operation').setLevel('ERROR')
#     src = get_absolute_project_directory("python-flask-adapter", "swagger_server", "swagger")
#     app = connexion.App(__name__, specification_dir=src)
#     app.app.json_encoder = JSONEncoder
#     app.add_api('swagger.yaml')
#     return app.app.test_client()


# Helpers for creating the json payload ***************

def get_describe(path):
    return ET.parse(os.path.join(path, "conf", "describe.xml")).getroot()


def get_connection(project):
    # TODO: Clean this up!
    describe = get_describe(project["path"])
    project.setdefault("connections", [])
    questions = [
        {
            "type": "list",
            "name": "connection",
            "message": "Which connection?",
            "choices": [connection["name"] for connection in project["connections"]] + ["New Connection"],
        }
    ]
    answers = prompt(questions, style=vrops_sdk_prompt_style)

    if answers["connection"] != "New Connection":
        return answers["connection"]

    def ns(kind):
        return "{http://schemas.vmware.com/vcops/schema}" + kind

    # TODO: We should handle when the 'CredentialKinds' element doesn't exist
    credential_kinds = describe.find(ns("CredentialKinds")).findall(ns("CredentialKind"))
    adapter_instance_kind = None

    for resource_kind in describe.find(ns("ResourceKinds")).findall(ns("ResourceKind")):
        if resource_kind.get("type") == "7":
            adapter_instance_kind = resource_kind

    if adapter_instance_kind is None:
        print("Cannot find adapter instance in conf/describe.xml.")
        print("Make sure the adapter instance resource kind exists and has tag 'type=\"7\"'.")
        exit(1)

    valid_credential_kind_keys = (adapter_instance_kind.get("credentialKind") or "").split(",")

    identifiers = adapter_instance_kind.findall(ns("ResourceIdentifier"))

    questions = []
    for identifier in sorted(identifiers, key=lambda i: int(i.get("dispOrder") or "100")):
        required = (identifier.get("required") or "true").lower() == "true"
        postfix = ": "
        if not required:
            postfix = " (Optional): "
        questions.append({
            "type": "input",
            "message": identifier.get("key") + postfix,
            "name": identifier.get("key"),
            "validate": lambda v: True if (not required) else (True if v else False),
        })

    identifiers = prompt(questions, style=vrops_sdk_prompt_style)
    credential_type = valid_credential_kind_keys[0]

    if len(valid_credential_kind_keys) > 1:
        questions = [{
            "type": "list",
            "message": "Which credential kind does this connection use?",
            "name": "credential_kind",
            "choices": valid_credential_kind_keys
        }]
        credential_type = prompt(questions, style=vrops_sdk_prompt_style)["credential_kind"]

    # Get credential Kind element
    credential_kind = [credential_kind for credential_kind in credential_kinds if
                       credential_kind.get("key") == credential_type]
    credentials = {}
    if len(credential_kind) == 1:
        credential_fields = credential_kind[0].findall(ns("CredentialField"))

        questions = []
        for credential_field in credential_fields:
            required = (credential_field.get("required") or "true").lower() == "true"
            postfix = ": "
            if not required:
                postfix = " (Optional): "
            password = (credential_field.get("password") or "false").lower() == "true"
            questions.append({
                "type": "input" if (not password) else "password",
                "message": credential_field.get("key") + postfix,
                "name": credential_field.get("key"),
                "validate": lambda v: True if (not required) else (True if v else False),
            })

        credentials = prompt(questions, style=vrops_sdk_prompt_style)

    questions = [
        {
            "type": "input",
            "name": "name",
            "message": "What should this connection be named?",
        }
    ]
    name = prompt(questions, style=vrops_sdk_prompt_style)["name"]
    new_connection = Connection(name, identifiers, credentials)
    project["connections"].append(new_connection.__dict__)
    record_project(project)
    return new_connection


def get_request_body(project, connection):
    # TODO: create this from the connection dict
    return {
        "adapterKey": {
            "name": "string",
            "adapterKind": "string",
            "objectKind": "string",
            "identifiers": [
                {
                    "key": "string",
                    "value": "string",
                    "isPartOfUniqueness": True
                }
            ]
        },
        "credentialConfig": {
            "credentialKey": "string",
            "credentialFields": [
                {
                    "key": "string",
                    "value": "string",
                    "isPassword": True
                }
            ]
        },
        "internalRestCredential": {
            "userName": "string",
            "password": "string"
        },
        "certificateConfig": {
            "certificates": []
        }
    }


def main():
    description = "Tool for running vROps test and collect methods outside of a collector container."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-p", "--path",
                        help="Path to root directory of project. " +
                             "Defaults to the current directory, or prompts if current directory is not a project.")
    # TODO: We need to mount a volume to the docker image to capture logs in the same manner that vROps does/will
    parser.add_argument("-v", "--verbose", help="Include extra logging.", action="store_true")
    methods = parser.add_subparsers(required=True)

    # Test method
    test_method = methods.add_parser("connect",
                                     help="Simulate the 'test connection' method being called by the vROps collector.")
    test_method.set_defaults(func=test)

    # Collect method
    collect_method = methods.add_parser("collect",
                                        help="Simulate the 'collect' method being called by the vROps collector.")

    # TODO: need to implement 'times' and 'wait'
    collect_method.add_argument("-n", "--times", help="Run the given method 'n' times.", type=int, default=1)
    collect_method.add_argument("-w", "--wait", help="Amount of time to wait between collections (in seconds).",
                                type=int, default=10)
    collect_method.set_defaults(func=collections)

    # Parse arguments
    arguments = parser.parse_args()
    arguments.func(arguments)


if __name__ == '__main__':
    main()
