__author__ = 'VMware, Inc.'
__copyright__ = 'Copyright 2022 VMware, Inc. All rights reserved.'

import argparse
import json
import logging
import os
import time
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
import urllib3
from docker import DockerClient
from docker.errors import ContainerError, APIError
from docker.models.containers import Container
from docker.models.images import Image
from flask import json
from prompt_toolkit.validation import ConditionalValidator
from requests import RequestException

import common.logging_format
from common import filesystem, constant
from common.constant import DEFAULT_PORT
from common.describe import get_describe, ns, get_adapter_instance, get_credential_kinds, get_identifiers, is_true
from common.docker_wrapper import init, build_image, DockerWrapperError
from common.project import get_project, Connection, record_project
from common.propertiesfile import load_properties
from common.statistics import CollectionStatistics
from common.timer import timed
from common.ui import selection_prompt, print_formatted as print_formatted, prompt
from common.validation.api_response_validation import validate_api_response
from common.validation.describe_checks import validate_describe, cross_check_collection_with_describe
from common.validation.input_validators import NotEmptyValidator, UniquenessValidator, ChainValidator, IntegerValidator
from common.validation.result import Result

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = common.logging_format.PTKHandler()
consoleHandler.setFormatter(common.logging_format.CustomFormatter())
logger.addHandler(consoleHandler)


def read_collection_files(collection_directory_path, start_time, end_time):
    entries = os.listdir(collection_directory_path)
    collection_files = filter(lambda e: e.lower().endswith(".json"), entries)
    collections_to_analyse = \
        filter(lambda _file: start_time >= datetime.strptime(_file.split(".json")[0], constant.DATE_FORMAT) <= end_time,
               collection_files)

    for f in collections_to_analyse:
        # TODO get collection object from Kyle's function
        logger.debug(f"analysing: {f}")


def long_run(project, connection, verbosity, collection_time, collection_interval):
    # TODO: Add flag to specify collection period statistics
    logger.debug("starting long run")
    if collection_time < collection_interval:
        times = 1
    else:
        times = collection_time // collection_interval

    logger.debug(f"number of collections to run: {times}")

    collections_directory_path = os.path.join(project.path, "collections")
    if not os.path.exists(collections_directory_path):
        logger.debug(f"Creating collections directory at: {collections_directory_path}")
        filesystem.mkdir(collections_directory_path)

    # TODO: restructure collection code
    # NOTE: we don't want to run validation on every collection
    start_time = datetime.now()
    while times > 0:
        logger.info(f"Running collection No. {times}")
        times -= 1
        request, response = post(url=f"http://localhost:{DEFAULT_PORT}/collect",
                                 json=get_request_body(project, connection),
                                 headers={"Accept": "application/json"})
        now = datetime.now().strftime(constant.DATE_FORMAT)
        logger.debug(f"request: {request}")
        logger.debug(f"response: {response}")
        with open(os.path.join(collections_directory_path, f"{now}.json"), "w", encoding="utf-8") as collection_result:
            json.dump(json.loads(response.text), collection_result, ensure_ascii=False, indent=4)

        next_collection = time.time() + collection_interval
        while time.time() < next_collection:
            remaining = time.strftime("%H:%M:%S", time.gmtime(next_collection - time.time()))
            print(f"Time until next collection: {remaining}", end="\r")
            time.sleep(.2)

    end_time = datetime.now()
    read_collection_files(collections_directory_path, start_time, end_time)
    # TODO: Read all collections ad generate statistics
    # TODO: Generate statistics


def run(arguments):
    # User input
    project = get_project(arguments)

    log_file_path = os.path.join(project.path, 'logs')
    if not os.path.exists(log_file_path):
        filesystem.mkdir(log_file_path)

    try:
        logging.basicConfig(filename=os.path.join(log_file_path, "test.log"),
                            filemode="a",
                            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
                            datefmt="%H:%M:%S",
                            level=logging.DEBUG)
    except Exception:
        logger.warning(f"Unable to save logs to {log_file_path}")

    connection = get_connection(project, arguments)
    method = get_method(arguments)
    verbosity = arguments.verbosity

    docker_client = init()

    image = get_container_image(docker_client, project.path)
    logger.info("Starting adapter HTTP server")
    container = run_image(docker_client, image, project.path)

    try:
        # Need time for the server to start
        started = False
        start_time = time.perf_counter()
        max_wait_time = 20
        while not started:
            try:
                version = json.loads(requests.get(
                    f"http://localhost:{DEFAULT_PORT}/apiVersion",
                    headers={"Accept": "application/json"}).text)
                started = True
                logger.info(f"HTTP Server started with api version "
                            f"{version['major']}.{version['minor']}.{version['maintenance']}")
            except (RequestException, ConnectionError) as e:
                elapsed_time = time.perf_counter() - start_time
                if elapsed_time > max_wait_time:
                    logger.error(f"HTTP Server did not start after {max_wait_time} seconds")
                    exit(1)
                logger.info("Waiting for HTTP server to start...")
                time.sleep(0.5)

        args = vars(arguments)
        # TODO: find a nicer way to write the logic for the long run
        if "long_run" in args and args["long_run"]:
            # TODO: Add suffixes to the parameters to determine hours minutes seconds to run
            long_run(project, connection, verbosity, args["collection_time"], args["collection_intervals"])
        else:
            method(project, connection, verbosity)
    finally:
        stop_container(container)
        docker_client.images.prune(filters={"label": "mp-test"})


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

def post_collect(project, connection, verbosity):
    request, response, elapsed_time = post(url=f"http://localhost:{DEFAULT_PORT}/collect",
                                           json=get_request_body(project, connection),
                                           headers={"Accept": "application/json"})
    process(request, response, elapsed_time,
            project=project,
            validators=[validate_api_response, cross_check_collection_with_describe],
            verbosity=verbosity)

    logger.info(CollectionStatistics(json.loads(response.text), elapsed_time))


def post_test(project, connection, verbosity):
    request, response, elapsed_time = post(url=f"http://localhost:{DEFAULT_PORT}/test",
                                           json=get_request_body(project, connection),
                                           headers={"Accept": "application/json"})
    process(request, response, elapsed_time,
            project=project,
            validators=[validate_api_response],
            verbosity=verbosity)


def post_endpoint_urls(project, connection, verbosity):
    request, response, elapsed_time = post(url=f"http://localhost:{DEFAULT_PORT}/endpointURLs",
                                           json=get_request_body(project, connection),
                                           headers={"Accept": "application/json"})
    process(request, response, elapsed_time,
            project=project,
            validators=[validate_api_response],
            verbosity=verbosity)


def get_version(project, connection, verbosity):
    request, response, elapsed_time = get(
        url=f"http://localhost:{DEFAULT_PORT}/apiVersion",
        headers={"Accept": "application/json"}
    )
    process(request, response, elapsed_time,
            project=project,
            validators=[validate_api_response],
            verbosity=verbosity)


def wait(project, connection, verbosity):
    input("Press enter to finish")


@timed
def get(url, headers):
    request = requests.models.Request(method="GET",
                                      url=url,
                                      headers=headers)
    response = requests.get(url=url, headers=headers)
    return request, response


@timed
def post(url, json, headers):
    request = requests.models.Request(method="POST", url=url,
                                      json=json,
                                      headers=headers)
    response = requests.post(url=url, json=json, headers=headers)
    return request, response


def process(request, response, elapsed_time, project, validators, verbosity):

    json_response = json.loads(response.text)
    logger.info(json.dumps(json_response, sort_keys=True, indent=3))
    logger.info(f"Request completed in {elapsed_time:0.2f} seconds.")

    result = Result()
    for validate in validators:
        result += validate(project, request, response)

    for severity, message in result.messages:
        if severity.value <= verbosity:
            if severity.value == 1:
                logger.error(message)
            elif severity.value == 2:
                logger.warning(message)
            else:
                logger.info(message)
    validation_file_path = os.path.join(project.path, "logs", "validation.log")
    write_validation_log(validation_file_path, result)

    if len(result.messages) > 0:
        logger.info(f"All validation logs written to '{validation_file_path}'")
    if result.error_count > 0 and verbosity < 1:
        logger.error(f"Found {result.error_count} errors when validating response")
    if result.warning_count > 0 and verbosity < 2:
        logger.warning(f"Found {result.warning_count} warnings when validating response")
    if result.error_count + result.warning_count == 0:
        logger.info("Validation passed with no errors", extra={"style": "class:success"})


def write_validation_log(validation_file_path, result):
    # TODO: create a test object to be able to write encapsulated test results
    with open(validation_file_path, "w") as validation_file:
        for (severity, message) in result.messages:
            validation_file.write(f"{severity.name}: {message}\n")


# Docker helpers ***************
def get_container_image(client: DockerClient, build_path: str) -> Image:
    with open(os.path.join(build_path, "manifest.txt")) as manifest_file:
        manifest = json.load(manifest_file)

    docker_image_tag = manifest["name"].lower() + "-test:" + manifest["version"]

    logger.info("Building adapter image")
    build_image(client, path=build_path, tag=docker_image_tag, nocache=False, labels={"mp-test": f"{time.time()}"})

    return docker_image_tag


def run_image(client: DockerClient, image: Image, path: str) -> Container:
    # Note: errors from running image (eg. if there is a process using port 8080 it will cause an error) are handled by the try/except block in the 'main' function
    return client.containers.run(image,
                                 detach=True,
                                 ports={"8080/tcp": DEFAULT_PORT},
                                 volumes={f"{path}/logs": {"bind": "/var/log/", "mode": "rw"}})


def stop_container(container: Container):
    container.kill()
    container.remove()


# Helpers for creating the json payload ***************

def get_connection(project, arguments):
    connection_names = [(connection.name, connection.name) for connection in project.connections]
    # We should ensure the describe is valid before parsing through it.
    validate_describe(project.path)
    describe = get_describe(project.path)
    resources = load_properties(os.path.join(project.path, "conf", "resources", "resources.properties"))

    if (arguments.connection, arguments.connection) not in connection_names:
        connection_name = selection_prompt("Choose a connection: ",
                                           connection_names + [("new_connection", "New Connection")])
    else:
        connection_name = arguments.connection

    if connection_name != "new_connection":
        for connection in project.connections:
            if connection.name == connection_name:
                return connection
        logger.error(f"Cannot find connection with name '{connection_name}'.")
        exit(1)

    adapter_instance_kind = get_adapter_instance(describe)
    if adapter_instance_kind is None:
        logger.error("Cannot find adapter instance in conf/describe.xml.")
        logger.error("Make sure the adapter instance resource kind exists and has tag 'type=\"7\"'.")
        exit(1)

    print_formatted("""Connections are akin to Adapter Instances in vROps, and contain the parameters needed to connect to a target
environment. As such, the following connection parameters and credential fields are derived from the
'conf/describe.xml' file and are specific to each Management Pack.""", "class:information", frame=True)

    identifiers = {}
    for identifier in sorted(get_identifiers(adapter_instance_kind), key=lambda i: int(i.get("dispOrder") or "100")):
        value = input_parameter("connection parameter", identifier, resources)

        identifiers[identifier.get("key")] = {
            "value": value,
            "required": is_true(identifier, "required", default="true"),
            "part_of_uniqueness": identifier.get("identType", "1") == "1"
        }

    valid_credential_kind_keys = (adapter_instance_kind.get("credentialKind") or "").split(",")
    credential_kinds = {credential_kind.get("key"): credential_kind
                        for credential_kind in get_credential_kinds(describe)
                        if credential_kind.get("key") in valid_credential_kind_keys}

    credential_type = valid_credential_kind_keys[0]

    if len(valid_credential_kind_keys) > 1:
        credential_type = selection_prompt("Select the credential kind for this connection: ",
                                           [(kind.get("key"), resources.get(kind.get("nameKey"), kind.get("key")))
                                            for kind in list(credential_kinds.values())])

    # Get credential Kind element
    credential_kind = credential_kinds.get(credential_type)
    credentials = {}
    if credential_kind is not None:
        credential_fields = credential_kind.findall(ns("CredentialField"))

        credentials["credential_kind_key"] = credential_type
        for credential_field in credential_fields:
            value = input_parameter("credential field", credential_field, resources)

            credentials[credential_field.get("key")] = {
                "value": value,
                "required": is_true(credential_field, "required", default="true"),
                "password": is_true(credential_field, "password")
            }

    connection_names = [connection.name for connection in (project.connections or [])]
    connection_names.append("New Connection")

    name = prompt(message="Enter a name for this connection: ",
                  validator=UniquenessValidator("Connection name", connection_names),
                  validate_while_typing=False,
                  description="The connection name is used to identify this connection (parameters and credential) in\n"
                              "command line arguments or in the interactive prompt.")
    new_connection = Connection(name, identifiers, credentials)
    project.connections.append(new_connection)
    record_project(project)
    return new_connection


def input_parameter(parameter_type, parameter, resources):
    key = parameter.get("key")
    is_required = is_true(parameter, "required", default="true")
    is_password = is_true(parameter, "password")
    postfix = ": " if is_required else " (Optional): "
    default = parameter.get("default", "")
    is_integer = parameter.get("type", "string") == "integer"
    is_enum = is_true(parameter, "enum")
    name_key = parameter.get("nameKey")
    label = resources.get(name_key, key)
    description = resources.get(f"{name_key}.description", "")

    if is_enum:
        enum_values = [(enum_value.get("value"), resources.get(enum_value.get("nameKey"), enum_value.get("value")))
                       for enum_value in parameter.findall(ns("enum"))]
        value = selection_prompt(f"Enter {parameter_type} '{label}'{postfix}", enum_values, description)
    else:
        value = prompt(message=f"Enter {parameter_type} '{label}'{postfix}",
                       default=default,
                       is_password=is_password,
                       validator=ChainValidator(
                           [ConditionalValidator(NotEmptyValidator(f"{parameter_type.capitalize()} '{label}'"),
                                                 is_required),
                            ConditionalValidator(IntegerValidator(f"{parameter_type.capitalize()} '{label}'"),
                                                 is_integer)]),
                       description=description)
    return value


def get_request_body(project, connection):
    describe = get_describe(project.path)
    adapter_instance = get_adapter_instance(describe)

    identifiers = []
    if connection.identifiers is not None:
        for key in connection.identifiers:
            identifiers.append({
                "key": key,
                "value": connection.identifiers[key]["value"],
                "isPartOfUniqueness": connection.identifiers[key]["part_of_uniqueness"]
            })

    credential_config = {}

    if connection.credential:
        fields = []
        for key in connection.credential:
            if key != "credential_kind_key":
                fields.append({
                    "key": key,
                    "value": connection.credential[key]["value"],
                    "isPassword": connection.credential[key]["password"]
                })
        credential_config = {
            "credentialKey": connection.credential["credential_kind_key"],
            "credentialFields": fields,
        }

    request_body = {
        "adapterKey": {
            "name": connection.name,
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
    parser.add_argument("-v", "--verbosity", help="Determine the amount of console logging when performing validation. "
                                                  "0: No console logging; 3: Max console logging.",
                        type=int, default=1,
                        choices=range(0, 4))

    methods = parser.add_subparsers(required=False)

    # Test method
    test_method = methods.add_parser("connect",
                                     help="Simulate the 'test connection' method being called by the vROps collector.")
    test_method.set_defaults(func=post_test)

    # Collect method
    collect_method = methods.add_parser("collect",
                                        help="Simulate the 'collect' method being called by the vROps collector.")

    collect_method.add_argument("-t", "--collection-time", help="Run the collection method for 't' seconds.",
                                type=int, default=600)
    collect_method.add_argument("-w", "--collection-intervals",
                                help="Amount of time to wait between collections (in seconds).",
                                type=int, default=10)

    # TODO: Re-structure this parameter
    collect_method.add_argument("-l", "--long-run",
                                help="triggers a long run",
                                type=bool, default=False)
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
        print_formatted("")
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
    except SystemExit as system_exit:
        exit(system_exit.code)
    except BaseException as base_error:
        print_formatted("Unexpected error")
        logger.error(base_error)
        traceback.print_tb(base_error.__traceback__)
        exit(1)


if __name__ == '__main__':
    main()
