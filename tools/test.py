__author__ = 'VMware, Inc.'
__copyright__ = 'Copyright 2022 VMware, Inc. All rights reserved.'

import argparse
import json
import os
import time
import xml.etree.ElementTree as ET

import docker
import requests
import urllib3
from PyInquirer import prompt
from flask import json
from jsonschema.exceptions import ValidationError
from openapi_schema_validator import validate
from requests import RequestException

from common.filesystem import get_absolute_project_directory
from common.project import get_project, Connection, record_project
from common.style import vrops_sdk_prompt_style

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def run(arguments):
    # User input
    project = get_project(arguments)
    connection = get_connection(project, arguments)
    method = get_method(arguments)

    docker_client = docker.client.from_env()
    print("Building adapter image")
    image = create_container_image(docker_client, project["path"])
    print("Starting adapter HTTP server")
    container = run_image(docker_client, image)

    try:
        # Need time for the server to start
        started = False
        start_time = time.perf_counter()
        max_wait_time = 20
        while not started:
            try:
                version = requests.get(
                    "http://localhost:8080/version",
                    headers={"Accept": "application/json"})
                started = True
                print(f"HTTP Server started with adapter version {version.text.strip()}.")
            except (RequestException, ConnectionError) as e:
                elapsed_time = time.perf_counter() - start_time
                if elapsed_time > max_wait_time:
                    print(f"HTTP Server did not start after {max_wait_time} seconds")
                    exit(1)
                print("Waiting for HTTP server to start...")
                time.sleep(0.5)

        args = vars(arguments)
        times = args.setdefault("times", 1)
        wait = args.setdefault("wait", 10)
        while times > 0:
            # Run connection test or collection test
            method(project, connection)
            times = times - 1
            if times > 0:
                print(f"{times} requests remaining. Waiting {wait} seconds until next request.")
                time.sleep(wait)
    except BaseException as e:
        print(e)
    finally:
        stop_container(container)


def get_method(arguments):
    method_question = [
        {
            "type": "list",
            "name": "method",
            "message": "Choose a method to test:",
            "choices": ["Test Connection", "Collect"],
            "filter": lambda m: post_test if m == "Test Connection" else post_collect
        }
    ]
    return vars(arguments).setdefault("func", prompt(method_question, style=vrops_sdk_prompt_style)["method"])


# REST calls ***************

def post_collect(project, connection):
    response = requests.post(
        "http://localhost:8080/collect",
        json=get_request_body(project, connection),
        headers={"Accept": "application/json"})
    handle_response(response)


def post_test(project, connection):
    response = requests.post(
        "http://localhost:8080/test",
        json=get_request_body(project, connection),
        headers={"Accept": "application/json"})
    handle_response(response)


def get_version(project, connection):
    response = requests.get(
        "http://localhost:8080/version",
        headers={"Accept": "application/json"})
    print(f"Adapter version: {response.text}")


def handle_response(response):
    json_response = json.loads(response.text)
    schema_file = get_absolute_project_directory("api", "vrops-collector-fwk2-openapi.json")
    with open(schema_file, "r") as schema:
        json_schema = json.load(schema)
        try:
            validate(json_response, json_schema)
            # TODO: Make this prettier (for people)?
            print(json_response)
        except ValidationError as v:
            print("Returned result does not conform to the schema:")
            print(v)


# Docker helpers ***************

def create_container_image(client, build_path):
    with open(os.path.join(build_path, "manifest.txt")) as manifest_file:
        manifest = json.load(manifest_file)

    # TODO: Only build image if sources have changed or a previous image does not exist,
    #       or mount the code directory and have it dynamically update.
    #       Either way, we should avoid building the image ever time this script is called
    # TODO: We need to mount a volume to the docker image to capture logs in the same manner that vROps does
    docker_image_tag = manifest["name"].lower() + ":" + manifest["version"] + "_" + str(time.time())
    client.images.build(path=build_path, nocache=True, rm=True, tag=docker_image_tag)
    return docker_image_tag


def run_image(client, image):
    return client.containers.run(image, detach=True, ports={"8080/tcp": 8080})


def stop_container(container):
    container.kill()


# Helpers for creating the json payload ***************

def get_describe(path):
    return ET.parse(os.path.join(path, "conf", "describe.xml")).getroot()


def ns(kind):
    return "{http://schemas.vmware.com/vcops/schema}" + kind


def get_connection(project, arguments):
    connection_names = [connection["name"] for connection in project["connections"]]
    describe = get_describe(project["path"])
    project.setdefault("connections", [])
    questions = [
        {
            "type": "list",
            "name": "connection",
            "message": "Choose a connection:",
            "choices": connection_names + ["New Connection"],
        }
    ]
    if arguments.connection not in connection_names:
        answers = prompt(questions, style=vrops_sdk_prompt_style)
    else:
        answers = {"connection": arguments.connection}

    if answers["connection"] != "New Connection":
        for connection in project["connections"]:
            if answers["connection"] == connection["name"]:
                return connection
        print(f"Cannot find connection corresponding to {answers['connection']}.")
        exit(1)

    adapter_instance_kind = get_adapter_instance(describe)
    if adapter_instance_kind is None:
        print("Cannot find adapter instance in conf/describe.xml.")
        print("Make sure the adapter instance resource kind exists and has tag 'type=\"7\"'.")
        exit(1)

    credential_kinds = get_credential_kinds(describe)
    valid_credential_kind_keys = (adapter_instance_kind.get("credentialKind") or "").split(",")

    identifiers = get_identifiers(adapter_instance_kind)

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
            "filter": lambda v: {
                "value": v,
                "required": required,
                "part_of_uniqueness": identifier.get("identType") == "1"
            }
        })

    identifiers = prompt(questions, style=vrops_sdk_prompt_style)
    credential_type = valid_credential_kind_keys[0]

    if len(valid_credential_kind_keys) > 1:
        questions = [{
            "type": "list",
            "message": "Select the credential kind for this connection:",
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
                "validate": lambda v: True if (not required) else (
                    True if v else "This field is required and cannot be blank."),
                "filter": lambda v: {"value": v, "required": required, "password": password}
            })

        credentials = prompt(questions, style=vrops_sdk_prompt_style)
        credentials["credential_kind_key"] = credential_type

    connection_names = list(map(lambda connection: connection["name"], (project["connections"] or [])))
    connection_names.append("New Connection")

    questions = [
        {
            "type": "input",
            "name": "name",
            "message": "Enter a name for this connection:",
            "validate": lambda connection_name: connection_name not in connection_names or "A connection with that "
                                                                                           "name already exists. "
        }
    ]
    name = prompt(questions, style=vrops_sdk_prompt_style)["name"]
    new_connection = Connection(name, identifiers, credentials).__dict__
    project["connections"].append(new_connection)
    record_project(project)
    return new_connection


def get_adapter_instance(describe):
    adapter_instance_kind = None

    for resource_kind in describe.find(ns("ResourceKinds")).findall(ns("ResourceKind")):
        if resource_kind.get("type") == "7":
            adapter_instance_kind = resource_kind

    return adapter_instance_kind


def get_identifiers(adapter_instance):
    return adapter_instance.findall(ns("ResourceIdentifier"))


def get_credential_kinds(describe):
    credential_kinds = describe.find(ns("CredentialKinds"))
    if credential_kinds is None:
        return None
    else:
        return credential_kinds.findall(ns("CredentialKind"))


def get_request_body(project, connection):
    describe = get_describe(project["path"])
    adapter_instance = get_adapter_instance(describe)

    identifiers = []
    if "identifiers" in connection and connection["identifiers"] is not None:
        for key in connection["identifiers"]:
            identifiers.append({
                "key": key,
                "value": connection["identifiers"][key]["value"],
                "isPartOfUniqueness": connection["identifiers"][key]["part_of_uniqueness"]
            })

    credential_config = {}

    if "credential" in connection and connection["credential"]:
        fields = []
        for key in connection["credential"]:
            if key != "credential_kind_key":
                fields.append({
                    "key": key,
                    "value": connection["credential"][key]["value"],
                    "isPassword": connection["credential"][key]["password"]
                })
        credential_config = {
            "credentialKey": connection["credential"]["credential_kind_key"],
            "credentialFields": fields,
        }

    request_body = {
        "adapterKey": {
            "name": connection["name"],
            "adapterKind": describe.get("key"),
            "objectKind": adapter_instance.get("key"),
            "identifiers": identifiers,
        },
        "internalRestCredential": {
            "userName": "string",
            "password": "string"
        },
        "certificateConfig": {
            "certificates": []
        }
    }
    if credential_config:
        request_body["credentialConfig"] = credential_config

    return request_body


def main():
    description = "Tool for running adapter test and collect methods outside of a vROps Cloud Proxy."
    parser = argparse.ArgumentParser(description=description)
    methods = parser.add_subparsers(required=False)

    # General options
    parser.add_argument("-p", "--path", help="Path to root directory of project. Defaults to the current directory, "
                                             "or prompts if current directory is not a project.")

    parser.add_argument("-c", "--connection", help="Name of a connection in this project.")

    # TODO: Hook this up to logging, once we have adapter logging. May want to set the level rather than verbose.
    # parser.add_argument("-v", "--verbose", help="Include extra logging.", action="store_true")

    # Test method
    test_method = methods.add_parser("connect",
                                     help="Simulate the 'test connection' method being called by the vROps collector.")
    test_method.set_defaults(func=post_test)

    # Collect method
    collect_method = methods.add_parser("collect",
                                        help="Simulate the 'collect' method being called by the vROps collector.")
    collect_method.add_argument("-n", "--times", help="Run the given method 'n' times.", type=int, default=1)
    collect_method.add_argument("-w", "--wait", help="Amount of time to wait between collections (in seconds).",
                                type=int, default=10)
    collect_method.set_defaults(func=post_collect)

    run(parser.parse_args())


if __name__ == '__main__':
    main()
