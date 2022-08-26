__author__ = 'VMware, Inc.'
__copyright__ = 'Copyright 2022 VMware, Inc. All rights reserved.'

#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import argparse
import asyncio
import json
import logging
import os
import time
import traceback
import xml.etree.ElementTree as ET

import httpx
import requests
import urllib3
from docker import DockerClient
from docker.errors import ContainerError, APIError
from docker.models.containers import Container
from docker.models.images import Image
from flask import json
from httpx import ReadTimeout, Response
from prompt_toolkit.validation import ConditionalValidator
from requests import RequestException, Request

from vrealize_operations_integration_sdk.constant import DEFAULT_PORT, API_VERSION_ENDPOINT, ENDPOINTS_URLS_ENDPOINT, \
    CONNECT_ENDPOINT, COLLECT_ENDPOINT, DEFAULT_MEMORY_LIMIT
from vrealize_operations_integration_sdk.containeraized_adapter_rest_api import send_get_to_adapter, \
    send_post_to_adapter
from vrealize_operations_integration_sdk.describe import get_describe, ns, get_adapter_instance, get_credential_kinds, \
    get_identifiers, is_true
from vrealize_operations_integration_sdk.docker_wrapper import init, build_image, DockerWrapperError, stop_container, \
    ContainerStats
from vrealize_operations_integration_sdk.filesystem import mkdir
from vrealize_operations_integration_sdk.logging_format import PTKHandler, CustomFormatter
from vrealize_operations_integration_sdk.project import get_project, Connection, record_project
from vrealize_operations_integration_sdk.propertiesfile import load_properties
from vrealize_operations_integration_sdk.serialization import CollectionBundle, VersionBundle, ConnectBundle, \
    EndpointURLsBundle, LongCollectionBundle
from vrealize_operations_integration_sdk.ui import selection_prompt, print_formatted as print_formatted, prompt, \
    countdown
from vrealize_operations_integration_sdk.validation.describe_checks import validate_describe
from vrealize_operations_integration_sdk.validation.input_validators import NotEmptyValidator, UniquenessValidator, \
    ChainValidator, IntegerValidator

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = PTKHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)


def get_sec(time_str):
    """Get seconds from time."""
    try:
        unit = time_str[-1]
        if unit == "s":
            return float(time_str[0:-1])
        elif unit == "m":
            return float(time_str[0:-1]) * 60
        elif unit == "h":
            return float(time_str[0:-1]) * 3600
        else:  # no unit specified, default to minutes
            return float(time_str) * 60
    except ValueError:
        logger.error("Invalid time. Time should be a numeric value in minutes, or a numeric value "
                     "followed by the unit 'h', 'm', or 's'.")
        exit(1)


async def run_long_collect(client, container, project, connection, **kwargs):
    logger.debug("Starting long run")
    cli_args = kwargs.get("cli_args")
    duration = get_sec(cli_args["duration"])
    collection_interval = get_sec(cli_args["collection_interval"])

    if duration < collection_interval:
        times = 1
    else:
        # Remove decimal points by casting number to integer, which behaves as a floor function
        times = int(duration / collection_interval)

    long_collection_bundle = LongCollectionBundle(collection_interval)
    for collection_no in range(1, times + 1):
        logger.info(f"Running collection No. {collection_no} of {times}")

        collection_bundle = await run_collect(client, container, project, connection)
        collection_bundle.collection_number = collection_no
        elapsed_time = collection_bundle.duration
        long_collection_bundle.add(collection_bundle)

        next_collection = time.time() + collection_interval - elapsed_time
        if elapsed_time > collection_interval:
            logger.warning("Collection took longer than the given collection interval")

        time_until_next_collection = next_collection - time.time()
        if time_until_next_collection > 0 and times != collection_no:
            countdown(time_until_next_collection, "Time until next collection: ")

    return long_collection_bundle


async def run_collect(client, container, project, connection, **kwargs) -> CollectionBundle:
    initial_container_stats = container.stats(stream=False)
    container_stats = ContainerStats(initial_container_stats)

    coroutine = send_post_to_adapter(client, project, connection, COLLECT_ENDPOINT)
    task = asyncio.create_task(coroutine)

    while not task.done():
        container_stats.add(container.stats(stream=False))
        await asyncio.sleep(.5)
    try:
        request, response, elapsed_time = await task
    except ReadTimeout as timeout:
        # Translate the error to a standard request response format (for validation purposes)
        timeout_request = timeout.request
        request = Request(method=timeout_request.method, url=timeout_request.url, headers=timeout_request.headers)
        response = Response(408)
        elapsed_time = timeout_request.extensions.get("timeout").get("read")

    collection_bundle = CollectionBundle(request=request, response=response, duration=elapsed_time,
                                         container_stats=container_stats)
    return collection_bundle


async def run_connect(client, project, connection, **kwargs):
    request, response, elapsed_time = await send_post_to_adapter(client, project, connection, CONNECT_ENDPOINT)

    return ConnectBundle(request, response, elapsed_time)


async def run_get_endpoint_urls(client, project, connection, **kwargs):
    request, response, elapsed_time = await send_post_to_adapter(client, project, connection, ENDPOINTS_URLS_ENDPOINT)
    return EndpointURLsBundle(request, response, elapsed_time)


async def run_get_server_version(client, **kwargs):
    request, response, elapsed_time = await send_get_to_adapter(client, API_VERSION_ENDPOINT)

    return VersionBundle(request, response, elapsed_time)


def run_wait(**kwargs):
    input("Press enter to finish")


async def run(arguments):
    # User input
    project = get_project(arguments)

    log_file_path = os.path.join(project.path, 'logs')
    if not os.path.exists(log_file_path):
        mkdir(log_file_path)

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

    memory_limit = connection.identifiers.get("container_memory_limit", DEFAULT_MEMORY_LIMIT)
    if type(memory_limit) is dict:
        memory_limit = memory_limit.get("value", DEFAULT_MEMORY_LIMIT)

    try:
        memory_limit = int(memory_limit)
        if memory_limit < 6:
            logger.warning(f"'container_memory_limit' of {memory_limit} MB is below the 6MB docker limit.")
            logger.warning(f"Using minimum value: 6 MB")
            memory_limit = 6
    except ValueError as e:
        logger.warning(f"Cannot set 'container_memory_limit': {e}")
        logger.warning(f"Using default value: {DEFAULT_MEMORY_LIMIT} MB")
        memory_limit = DEFAULT_MEMORY_LIMIT

    container = run_image(docker_client, image, project.path, memory_limit)

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

        # Get certificates and add to connection if we are running any of the test or collect methods
        # We will distinguish between 'None' (endpointURLs has not been called) and '[]' (endpointURLs has been
        # called but no certificates were found).
        if method in [run_connect, run_collect, run_long_collect] and connection.certificates is None:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    endpoints = await run_get_endpoint_urls(client, project, connection)
                    certificates = endpoints.retrieve_certificates()
                    connection.certificates = certificates
                    # Record certificates in connection to omit this step next time.
                    # Certificates can be regenerated by removing the 'certificates' key
                    # from the connection.
                    project.record()
            except Exception as e:
                logger.warning(f"Caught exception when retrieving SSL certificates: {e}.")
        if connection.certificates is None:
            logger.warning(f"Error retrieving SSL certificates from 'endpointURLs'. "
                           f"Proceeding without certificates.")

        # async event loop
        args = vars(arguments)
        timeout = args.get("timeout", None)
        if timeout is not None:
            timeout = get_sec(timeout)
        elif method == run_long_collect:
            timeout = 1.5 * get_sec(args.get("collection_interval"))

        async with httpx.AsyncClient(timeout=timeout) as client:
            result_bundle = await method(client=client,
                                         container=container,
                                         project=project,
                                         connection=connection,
                                         verbosity=verbosity,
                                         cli_args=vars(arguments))
    finally:
        stop_container(container)
        docker_client.images.prune(filters={"label": "mp-test"})

    # TODO: Add UI code here
    logger.info(result_bundle)
    if type(result_bundle) is not LongCollectionBundle:
        # TODO: This logic should be performed in the UI
        ui_validation(result_bundle.validate(project),
                      project,
                      os.path.join(project.path, "logs", "validation.log"),
                      verbosity)


def get_method(arguments):
    if "func" in vars(arguments):
        return vars(arguments)["func"]

    return selection_prompt(
        "Choose a method to test:",
        [(run_connect, "Test Connection"),
         (run_collect, "Collect"),
         (run_long_collect, "Long Run Collection"),
         (run_get_endpoint_urls, "Endpoint URLs"),
         (run_get_server_version, "Version")])


# TODO: move this to UI
def ui_validation(result, project, validation_file_path, verbosity):
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


# TODO: move this to UI
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


def run_image(client: DockerClient, image: Image, path: str,
              container_memory_limit: int = DEFAULT_MEMORY_LIMIT) -> Container:
    # Note: errors from running image (e.g., if there is a process using port 8080 it will cause an error) are handled
    # by the try/except block in the 'main' function

    memory_limit = DEFAULT_MEMORY_LIMIT
    if container_memory_limit:
        memory_limit = container_memory_limit

    # Docker memory parameters expect a unit ('m' is 'MB'), or the number will be interpreted as bytes
    # vROps sets the swap memory limit to the memory limit + 512MB, so we will also. The swap memory
    # setting is a combination of memory and swap, so this will limit swap space to a max of 512MB regardless
    # of the memory limit.
    return client.containers.run(image,
                                 detach=True,
                                 ports={"8080/tcp": DEFAULT_PORT},
                                 mem_limit=f"{memory_limit}m",
                                 memswap_limit=f"{memory_limit + 512}m",
                                 volumes={f"{path}/logs": {"bind": "/var/log/", "mode": "rw"}})


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
    test_method.set_defaults(func=run_connect)
    test_method.add_argument("-t", "--timeout",
                             help="Timeout limit for REST request performed.",
                             type=str, default="30s")

    # Collect method
    collect_method = methods.add_parser("collect",
                                        help="Simulate the 'collect' method being called by the vROps collector.")
    collect_method.set_defaults(func=run_collect)
    collect_method.add_argument("-t", "--timeout",
                                help="Timeout limit for REST request performed.",
                                type=str, default="5m")

    # Long run method
    long_run_method = methods.add_parser("long-run",
                                         help="Simulate a long run collection and return data statistics about the "
                                              "overall collection.")
    long_run_method.set_defaults(func=run_long_collect)

    long_run_method.add_argument("-d", "--duration",
                                 help="Duration of the long run in h hours, m minutes, or s seconds.",
                                 type=str, default="6h")

    long_run_method.add_argument("-i", "--collection-interval",
                                 help="Amount of time to wait between collections.",
                                 type=str, default="5m")

    long_run_method.add_argument("-t", "--timeout",
                                 help="Timeout limit for REST request performed. By default, the timeout will be set "
                                      "to 1.5 the time of a collection interval.",
                                 type=str)

    # URL Endpoints method
    url_method = methods.add_parser("endpoint_urls",
                                    help="Simulate the 'endpoint_urls' method being called by the vROps collector.")
    url_method.set_defaults(func=run_get_endpoint_urls)
    url_method.add_argument("-t", "--timeout",
                            help="Timeout limit for REST request performed.",
                            type=str, default="30s")

    # Version method
    version_method = methods.add_parser("version",
                                        help="Simulate the 'version' method being called by the vROps collector.")
    version_method.set_defaults(func=run_get_server_version)
    version_method.add_argument("-t", "--timeout",
                                help="Timeout limit for REST request performed.",
                                type=str, default="30s")

    # wait
    wait_method = methods.add_parser("wait",
                                     help="Simulate the adapter running on a vROps collector and wait for user input "
                                          "to stop. Useful for calling REST methods via an external tool, such as "
                                          "Insomnia or Postman.")
    wait_method.set_defaults(func=run_wait)

    try:
        asyncio.run(run(parser.parse_args()))
    except KeyboardInterrupt:
        logger.debug("Ctrl C pressed by user")
        print_formatted("")
        logger.info("Testing cancelled")
        exit(1)
    except DockerWrapperError as docker_error:
        logger.error("Unable to build container")
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
