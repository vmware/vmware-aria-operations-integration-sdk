__author__ = 'VMware, Inc.'
__copyright__ = 'Copyright 2022 VMware, Inc. All rights reserved.'

import argparse
import json
import os
import time
import xml.etree.ElementTree as ET
from json import JSONDecodeError
from pprint import pprint

import docker
import logging
import openapi_core
import requests
import urllib3
from PyInquirer import prompt
from docker import DockerClient
from docker.errors import ContainerError, APIError
from docker.models.containers import Container
from docker.models.images import Image
from flask import json
from openapi_core.contrib.requests import RequestsOpenAPIRequest, RequestsOpenAPIResponse
from openapi_core.validation.response.validators import ResponseValidator
from requests import RequestException

from common.constant import DEFAULT_PORT
from common.docker_wrapper import init, build_image, BuildError, InitError
from common.filesystem import get_absolute_project_directory
from common.project import get_project, Connection, record_project
from common.style import vrops_sdk_prompt_style

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


def with_keyboard_interrupt(ans):
    # TODO: Revisit this logic when we stop using PyInquirer
    if len(ans) == 0:
        raise KeyboardInterrupt
    else:
        return ans


def run(arguments):
    # User input
    project = get_project(arguments)
    connection = get_connection(project, arguments)
    method = get_method(arguments)

    docker_client = init()
    print("Building adapter image")
    image = create_container_image(docker_client, project["path"])
    print("Starting adapter HTTP server")
    container = run_image(docker_client, image, project["path"])

    try:
        # Need time for the server to start
        started = False
        start_time = time.perf_counter()
        max_wait_time = 20
        while not started:
            try:
                version = requests.get(
                    f"http://localhost:{DEFAULT_PORT}/apiVersion",
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
    finally:
        stop_container(container)


def get_method(arguments):
    if "func" in vars(arguments):
        return vars(arguments)["func"]

    ans = with_keyboard_interrupt(prompt([
        {
            "type": "list",
            "name": "method",
            "message": "Choose a method to test:",
            "choices": ["Test Connection", "Collect", "Endpoint URLs", "Version"],
        }], style=vrops_sdk_prompt_style))

    if ans["method"] == "Test Connection":
        return post_test
    elif ans["method"] == "Collect":
        return post_collect
    elif ans["method"] == "Endpoint URLs":
        return post_endpoint_urls
    else:
        return get_version


# REST calls ***************

def post_collect(project, connection):
    post(url=f"http://localhost:{DEFAULT_PORT}/collect",
         json=get_request_body(project, connection),
         headers={"Accept": "application/json"})


def post_test(project, connection):
    post(url=f"http://localhost:{DEFAULT_PORT}/test",
         json=get_request_body(project, connection),
         headers={"Accept": "application/json"})


def post_endpoint_urls(project, connection):
    post(url=f"http://localhost:{DEFAULT_PORT}/endpointURLs",
         json=get_request_body(project, connection),
         headers={"Accept": "application/json"})


def get_version(project, connection):
    response = requests.get(
        f"http://localhost:{DEFAULT_PORT}/apiVersion",
        headers={"Accept": "application/json"})
    print(f"Adapter version: {response.text}")


def wait(project, connection):
    input("Press enter to finish")


def post(url, json, headers):
    request = requests.models.Request(method="POST", url=url,
                                      json=json,
                                      headers=headers)
    response = requests.post(url=url, json=json, headers=headers)
    handle_response(request, response)


def handle_response(request, response):
    schema_file = get_absolute_project_directory("api", "vrops-collector-fwk2-openapi.json")
    with open(schema_file, "r") as schema:
        try:
            json_response = json.loads(response.text)
            print(json.dumps(json_response, sort_keys=True, indent=3))

            json_schema = json.load(schema)
            spec = openapi_core.create_spec(json_schema, validate_spec=True)
            validator = ResponseValidator(spec)
            openapi_request = RequestsOpenAPIRequest(request)
            openapi_response = RequestsOpenAPIResponse(response)
            validation = validator.validate(openapi_request, openapi_response)
            if validation.errors is not None and len(validation.errors) > 0:
                print("Validation failed: ")
                for error in validation.errors:
                    if "schema_errors" in vars(error):
                        pprint(vars(error)["schema_errors"])
                    else:
                        pprint(error)
        except JSONDecodeError as d:
            print("Returned result is not valid json:")
            print("Response:")
            print(repr(response.text))
            print(f"Error: {d}")


# Docker helpers ***************


def create_container_image(client: DockerClient, build_path: str) -> Image:
    with open(os.path.join(build_path, "manifest.txt")) as manifest_file:
        manifest = json.load(manifest_file)

    # TODO: Only build image if sources have changed or a previous image does not exist,
    #       or mount the code directory and have it dynamically update.
    #       Either way, we should avoid building the image ever time this script is called
    docker_image_tag = manifest["name"].lower() + ":" + manifest["version"] + "_" + str(time.time())
    build_image(client, path=build_path, tag=docker_image_tag)
    return docker_image_tag


def run_image(client: DockerClient, image: Image, path: str) -> Container:
    # TODO: handle errors from running image eg. if there is a process using port 8080 it will cause an error
    return client.containers.run(image,
                                 detach=True,
                                 ports={"8080/tcp": DEFAULT_PORT},
                                 volumes={f"{path}/logs": {"bind": "/var/log/", "mode": "rw"}})


def stop_container(container: Container):
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
        answers = with_keyboard_interrupt(prompt(questions, style=vrops_sdk_prompt_style))
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
        postfix = "': "
        if not required:
            postfix = "' (Optional): "
        questions.append({
            "type": "input",
            "message": "Enter connection parameter '" + identifier.get("key") + postfix,
            "name": identifier.get("key"),
            "validate": lambda v: True if (not required) else (
                True if v else "Parameter is required and cannot be blank."),
            "filter": lambda v: {
                "value": v,
                "required": required,
                "part_of_uniqueness": identifier.get("identType") == "1"
            }
        })

    identifiers = with_keyboard_interrupt(prompt(questions, style=vrops_sdk_prompt_style))

    credential_type = valid_credential_kind_keys[0]

    if len(valid_credential_kind_keys) > 1:
        questions = [{
            "type": "list",
            "message": "Select the credential kind for this connection:",
            "name": "credential_kind",
            "choices": valid_credential_kind_keys
        }]
        credential_type = with_keyboard_interrupt(prompt(questions, style=vrops_sdk_prompt_style))["credential_kind"]

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

        credentials = with_keyboard_interrupt(prompt(questions, style=vrops_sdk_prompt_style))

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
    name = with_keyboard_interrupt(prompt(questions, style=vrops_sdk_prompt_style))["name"]
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
        return []
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
        "clusterConnectionInfo": {
            "userName": "string",
            "password": "string",
            "hostName": "string"
        },
        "certificateConfig": {
            "certificates": []
        }
    }
    if credential_config:
        request_body["credentialConfig"] = credential_config

    return request_body


def main():
    try:
        logging.basicConfig(filename="logs/test.log",
                            filemode="a",
                            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
                            datefmt="%H:%M:%S",
                            level=logging.DEBUG)
    except Exception:
        logging.basicConfig(level=logging.CRITICAL + 1)

    description = "Tool for running adapter test and collect methods outside of a vROps Cloud Proxy."
    parser = argparse.ArgumentParser(description=description)

    # General options
    parser.add_argument("-p", "--path", help="Path to root directory of project. Defaults to the current directory, "
                                             "or prompts if current directory is not a project.")

    parser.add_argument("-c", "--connection", help="Name of a connection in this project.")

    # TODO: Hook this up to logging, once we have adapter logging. May want to set the level rather than verbose.
    # parser.add_argument("-v", "--verbose", help="Include extra logging.", action="store_true")

    methods = parser.add_subparsers(required=False)

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

    # URL Endpoints method
    url_method = methods.add_parser("endpoint_urls",
                                    help="Simulate the 'endpoint_urls' method being called by the vROps collector.")
    url_method.set_defaults(func=post_endpoint_urls)

    # Version method
    url_method = methods.add_parser("version",
                                    help="Simulate the 'version' method being called by the vROps collector.")
    url_method.set_defaults(func=get_version)

    # wait
    url_method = methods.add_parser("wait",
                                    help="Simulate the adapter running on a vROps collector and wait for user input "
                                         "to stop. Useful for calling REST methods via an external tool, such as "
                                         "Insomnia or Postman.")
    url_method.set_defaults(func=wait)

    try:
        run(parser.parse_args())
    except KeyboardInterrupt:
        logger.debug("Ctrl C pressed by user")
        print("\nTesting canceled")
        exit(0)
    except (InitError, BuildError) as docker_error:
        logger.error("Unable to build pak file")
        logger.error(f"{docker_error.args['message']}")
        logger.error(f"{docker_error.args['recommendation']}")
        exit(1)
    except (ContainerError, APIError) as skd_error:
        logger.error("Unable to run container")
        logger.error(f"SDK message: {skd_error}")
        exit(1)
    except BaseException as base_error:
        logger.error(base_error)
        exit(1)




if __name__ == '__main__':
    main()
