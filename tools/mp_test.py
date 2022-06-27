__author__ = 'VMware, Inc.'
__copyright__ = 'Copyright 2022 VMware, Inc. All rights reserved.'

import argparse
import json
import os
import time
import hashlib
import xml.etree.ElementTree as ET
from json import JSONDecodeError

import logging
import openapi_core
import requests
import urllib3
from docker import DockerClient
from docker.errors import ContainerError, APIError
from docker.models.containers import Container
from docker.models.images import Image
from flask import json
from openapi_core.contrib.requests import RequestsOpenAPIRequest, RequestsOpenAPIResponse
from openapi_core.validation.response.validators import ResponseValidator
from prompt_toolkit import prompt
from prompt_toolkit.validation import ConditionalValidator
from requests import RequestException

from common.describe import validate_describe, get_describe, ns, get_adapter_instance, get_credential_kinds, \
    get_identifiers, cross_check_collection_with_describe
from common.constant import DEFAULT_PORT
from common.docker_wrapper import init, build_image, DockerWrapperError
from common.filesystem import get_absolute_project_directory
from common.project import get_project, Connection, record_project
from common.ui import selection_prompt, print_formatted as print
from common.validators import NotEmptyValidator, UniquenessValidator, ChainValidator, IntegerValidator

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = logging.StreamHandler()
logger.addHandler(consoleHandler)


def hash_file(file):
    BUF_SIZE = 65536

    sha256 = hashlib.sha256()

    with open(file, 'rb') as f:

        while True:
            data = f.read(BUF_SIZE)

            if not data:
                break

            sha256.update(data)
    return sha256.hexdigest()


def unique_files_hash(path):
    # check if commands.cfg or adapter_requirements.txt changed
    # TODO : get unique files from project when supporting other languages
    unique_files = ["commands.cfg", "adapter_requirements.txt"]
    unique_files.sort()  # We should ensure the files order is always the same

    sha256 = hashlib.sha256()
    for file in unique_files:
        sha256.update(hash_file(os.path.join(path, file)).encode())

    return sha256.hexdigest()


def run(arguments):
    # User input
    project = get_project(arguments)
    try:
        logging.basicConfig(filename=f"{project['path']}/logs/test.log",
                            filemode="a",
                            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
                            datefmt="%H:%M:%S",
                            level=logging.DEBUG)
    except Exception:
        logging.basicConfig(level=logging.CRITICAL + 1)

    connection = get_connection(project, arguments)
    method = get_method(arguments)

    docker_client = init()

    image = get_container_image(docker_client, project['path'])
    logger.info("Starting adapter HTTP server")
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
                logger.info(f"HTTP Server started with adapter version {version.text.strip()}.")
            except (RequestException, ConnectionError) as e:
                elapsed_time = time.perf_counter() - start_time
                if elapsed_time > max_wait_time:
                    logger.error(f"HTTP Server did not start after {max_wait_time} seconds")
                    exit(1)
                logger.info("Waiting for HTTP server to start...")
                time.sleep(0.5)

        args = vars(arguments)
        times = args.setdefault("times", 1)
        wait = args.setdefault("wait", 10)
        while times > 0:
            # Run connection test or collection test
            method(project, connection)
            times = times - 1
            if times > 0:
                logger.info(f"{times} requests remaining. Waiting {wait} seconds until next request.")
                time.sleep(wait)
    finally:
        stop_container(container)


def get_method(arguments):
    if "func" in vars(arguments):
        return vars(arguments)["func"]

    return selection_prompt(
        "Choose a method to test:",
        [(post_test, "Test Connection"),
         (post_collect, "Collect"),
         (post_endpoint_urls, "Endpoint URLs"),
         (get_version, "Version")])


# REST calls ***************

def post_collect(project, connection):
    post(url=f"http://localhost:{DEFAULT_PORT}/collect",
         json=get_request_body(project, connection),
         headers={"Accept": "application/json"},
         project=project,
         validators=[validate_api_response, cross_check_collection_with_describe])


def post_test(project, connection):
    post(url=f"http://localhost:{DEFAULT_PORT}/test",
         json=get_request_body(project, connection),
         headers={"Accept": "application/json"},
         project=project,
         validators=[validate_api_response])


def post_endpoint_urls(project, connection):
    post(url=f"http://localhost:{DEFAULT_PORT}/endpointURLs",
         json=get_request_body(project, connection),
         headers={"Accept": "application/json"},
         project=project,
         validators=[validate_api_response])


def get_version(project, connection):
    response = requests.get(
        f"http://localhost:{DEFAULT_PORT}/apiVersion",
        headers={"Accept": "application/json"})
    logger.info(f"Adapter version: {response.text}")


def wait(project, connection):
    input("Press enter to finish")


def post(url, json, headers, project, validators):
    request = requests.models.Request(method="POST", url=url,
                                      json=json,
                                      headers=headers)
    response = requests.post(url=url, json=json, headers=headers)

    for validate in validators:
        validate(project, request, response)


def validate_api_response(project, request, response):
    schema_file = get_absolute_project_directory("api", "vrops-collector-fwk2-openapi.json")
    with open(schema_file, "r") as schema:
        try:
            json_response = json.loads(response.text)
            logger.info(json.dumps(json_response, sort_keys=True, indent=3))

            json_schema = json.load(schema)
            spec = openapi_core.create_spec(json_schema, validate_spec=True)
            validator = ResponseValidator(spec)
            openapi_request = RequestsOpenAPIRequest(request)
            openapi_response = RequestsOpenAPIResponse(response)
            validation = validator.validate(openapi_request, openapi_response)
            if validation.errors is not None and len(validation.errors) > 0:
                logger.info("Validation failed: ")
                for error in validation.errors:
                    if "schema_errors" in vars(error):
                        logger.info(vars(error)["schema_errors"])
                    else:
                        logger.info(error)
        except JSONDecodeError as d:
            logger.error("Returned result is not valid json:")
            logger.error("Response:")
            logger.error(repr(response.text))
            logger.error(f"Error: {d}")


# Docker helpers ***************
def get_container_image(client: DockerClient, build_path: str) -> Image:
    with open(os.path.join(build_path, "manifest.txt")) as manifest_file:
        manifest = json.load(manifest_file)

    docker_image_tag = manifest["name"].lower() + "-test:" + manifest["version"] + "-" + unique_files_hash(build_path)

    test_images = [image.attrs["RepoTags"][0] for image in client.images.list(name=f"{manifest['name'].lower()}-test")]
    if docker_image_tag not in test_images:
        for image in test_images:
            logger.info(f"Removing old test image {image} from docker")
            client.images.remove(image)

        logger.info("Building adapter image")
        build_image(client, path=build_path, tag=docker_image_tag)
    else:
        logger.info("Reusing Image")
        logger.debug(f"Reused image tag: {docker_image_tag}")

    return docker_image_tag


def run_image(client: DockerClient, image: Image, path: str) -> Container:
    # Note: errors from running image (eg. if there is a process using port 8080 it will cause an error) are handled by the try/except block in the 'main' function
    return client.containers.run(image,
                                 detach=True,
                                 ports={"8080/tcp": DEFAULT_PORT},
                                 volumes={
                                     f"{path}/logs": {"bind": "/var/log/", "mode": "rw"},
                                     # TODO: use the right path based on src code structure (language dependent)
                                     f"{path}/app": {"bind": "/home/vrops-adapter-user/src/app/app", "mode": "ro"}
                                 })


def stop_container(container: Container):
    container.kill()
    container.remove()


# Helpers for creating the json payload ***************

def get_connection(project, arguments):
    connection_names = [(connection["name"], connection["name"]) for connection in project["connections"]]
    # We should ensure the describe is valid before parsing through it.
    validate_describe(project["path"])
    describe = get_describe(project["path"])
    project.setdefault("connections", [])

    if (arguments.connection, arguments.connection) not in connection_names:
        connection = selection_prompt("Choose a connection: ",
                                      connection_names + [("new_connection", "New Connection")])
    else:
        connection = arguments.connection

    if connection != "new_connection":
        for _connection in project["connections"]:
            if _connection["name"] == connection:
                return _connection
        logger.error(f"Cannot find connection corresponding to {connection}.")
        exit(1)

    adapter_instance_kind = get_adapter_instance(describe)
    if adapter_instance_kind is None:
        logger.error("Cannot find adapter instance in conf/describe.xml.")
        logger.error("Make sure the adapter instance resource kind exists and has tag 'type=\"7\"'.")
        exit(1)

    credential_kinds = get_credential_kinds(describe)
    valid_credential_kind_keys = (adapter_instance_kind.get("credentialKind") or "").split(",")

    print("""
    Connections are akin to Adapter Instances in vROps, and contain the parameters needed to connect to a target
    envrironment. As such, the following connection parameters and credential fields are derived from the
    'conf/describe.xml' file and are specific to each Management Pack.
    """, "fg:ansidarkgray")

    # TODO: Parse resources.properties and use nameKey labels (if they exist) for UI purposes.
    #       If we do this we can also use the <nameKey>.description text here too for additional explanation.

    identifiers = {}
    for identifier in sorted(get_identifiers(adapter_instance_kind), key=lambda i: int(i.get("dispOrder") or "100")):
        key = identifier.get("key")
        is_required = (identifier.get("required") or "true").lower() == "true"
        postfix = "': " if is_required else "' (Optional): "
        default = identifier.get("default") or ""
        is_integer = (identifier.get("type") or "string") == "integer"
        is_enum = (identifier.get("enum") or "false").lower() == "true"

        if is_enum:
            enum_values = [(enum_value.get("value"), enum_value.get("value")) for enum_value in
                           identifier.findall(ns("enum"))]
            value = selection_prompt("Enter connection parameter '" + key + postfix, enum_values)
        else:
            value = prompt(message="Enter connection parameter '" + key + postfix,
                           default=default,
                           validator=ChainValidator(
                               [ConditionalValidator(NotEmptyValidator(f"Parameter '{key}'"), is_required),
                                ConditionalValidator(IntegerValidator(f"Parameter '{key}'"), is_integer)]))

        identifiers[key] = {
            "value": value,
            "required": is_required,
            "part_of_uniqueness": identifier.get("identType") == "1"
        }

    credential_type = valid_credential_kind_keys[0]

    if len(valid_credential_kind_keys) > 1:
        credential_type = selection_prompt("Select the credential kind for this connection: ",
                                           [(kind_key, kind_key) for kind_key in valid_credential_kind_keys])

    # Get credential Kind element
    credential_kind = [credential_kind for credential_kind in credential_kinds if
                       credential_kind.get("key") == credential_type]
    credentials = {}
    if len(credential_kind) == 1:
        credential_fields = credential_kind[0].findall(ns("CredentialField"))

        credentials["credential_kind_key"] = credential_type
        for credential_field in credential_fields:
            key = credential_field.get("key")
            is_required = (credential_field.get("required") or "true").lower() == "true"
            is_password = (credential_field.get("password") or "false").lower() == "true"
            postfix = "': " if is_required else "' (Optional): "

            value = prompt(message="Enter credential field '" + key + postfix,
                           is_password=is_password,
                           validator=ConditionalValidator(NotEmptyValidator(f"Credential field '{key}'"), is_required))

            credentials[key] = {
                "value": value,
                "required": is_required,
                "password": is_password
            }

    connection_names = [connection["name"] for connection in (project["connections"] or [])]
    connection_names.append("New Connection")

    name = prompt(message="Enter a name for this connection: ",
                  validator=UniquenessValidator("Connection name", connection_names),
                  validate_while_typing=False)
    new_connection = Connection(name, identifiers, credentials).__dict__
    project["connections"].append(new_connection)
    record_project(project)
    return new_connection


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
        print("")
        logger.info("Testing cancelled")
        exit(1)
    except DockerWrapperError as docker_error:
        logger.error("Unable to build pak file")
        logger.error(f"{docker_error.message}")
        logger.error(f"{docker_error.recommendation}")
        exit(1)
    except (ContainerError, APIError) as skd_error:
        logger.error("Unable to run container")
        logger.error(f"SDK message: {skd_error}")
        exit(1)
    except ET.ParseError as describe_error:
        logger.error(f"Unable to parse describe.xml: {describe_error}")
    except BaseException as base_error:
        logger.error(base_error)
        exit(1)


if __name__ == '__main__':
    main()
