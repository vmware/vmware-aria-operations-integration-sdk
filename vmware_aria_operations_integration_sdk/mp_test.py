#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import argparse
import asyncio
import logging
import os
import time
import traceback
from logging.handlers import RotatingFileHandler
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Tuple
from xml.etree.ElementTree import Element

import httpx
import lxml.etree as ET
import pkg_resources
import urllib3
from docker.errors import APIError
from docker.errors import ContainerError
from prompt_toolkit.validation import ConditionalValidator
from prompt_toolkit.validation import ValidationError
from xmlschema import XMLSchemaValidationError

from vmware_aria_operations_integration_sdk.adapter_container import AdapterContainer
from vmware_aria_operations_integration_sdk.config import get_config_value
from vmware_aria_operations_integration_sdk.config import set_config_value
from vmware_aria_operations_integration_sdk.constant import ADAPTER_DEFINITION_ENDPOINT
from vmware_aria_operations_integration_sdk.constant import API_VERSION_ENDPOINT
from vmware_aria_operations_integration_sdk.constant import COLLECT_ENDPOINT
from vmware_aria_operations_integration_sdk.constant import (
    CONFIG_SUITE_API_HOSTNAME_KEY,
)
from vmware_aria_operations_integration_sdk.constant import (
    CONFIG_SUITE_API_PASSWORD_KEY,
)
from vmware_aria_operations_integration_sdk.constant import (
    CONFIG_SUITE_API_USERNAME_KEY,
)
from vmware_aria_operations_integration_sdk.constant import CONNECT_ENDPOINT
from vmware_aria_operations_integration_sdk.constant import ENDPOINTS_URLS_ENDPOINT
from vmware_aria_operations_integration_sdk.containerized_adapter_rest_api import (
    send_get_to_adapter,
)
from vmware_aria_operations_integration_sdk.containerized_adapter_rest_api import (
    send_post_to_adapter,
)
from vmware_aria_operations_integration_sdk.describe import Describe
from vmware_aria_operations_integration_sdk.describe import get_adapter_instance
from vmware_aria_operations_integration_sdk.describe import get_credential_kinds
from vmware_aria_operations_integration_sdk.describe import get_identifiers
from vmware_aria_operations_integration_sdk.describe import is_true
from vmware_aria_operations_integration_sdk.describe import ns
from vmware_aria_operations_integration_sdk.docker_wrapper import DockerWrapperError
from vmware_aria_operations_integration_sdk.filesystem import mkdir
from vmware_aria_operations_integration_sdk.logging_format import CustomFormatter
from vmware_aria_operations_integration_sdk.logging_format import PTKHandler
from vmware_aria_operations_integration_sdk.project import Connection
from vmware_aria_operations_integration_sdk.project import get_project
from vmware_aria_operations_integration_sdk.project import Project
from vmware_aria_operations_integration_sdk.project import record_project
from vmware_aria_operations_integration_sdk.serialization import AdapterDefinitionBundle
from vmware_aria_operations_integration_sdk.serialization import CollectionBundle
from vmware_aria_operations_integration_sdk.serialization import ConnectBundle
from vmware_aria_operations_integration_sdk.serialization import EndpointURLsBundle
from vmware_aria_operations_integration_sdk.serialization import LongCollectionBundle
from vmware_aria_operations_integration_sdk.serialization import ResponseBundle
from vmware_aria_operations_integration_sdk.serialization import VersionBundle
from vmware_aria_operations_integration_sdk.serialization import WaitBundle
from vmware_aria_operations_integration_sdk.ui import countdown
from vmware_aria_operations_integration_sdk.ui import print_formatted as print_formatted
from vmware_aria_operations_integration_sdk.ui import prompt
from vmware_aria_operations_integration_sdk.ui import selection_prompt
from vmware_aria_operations_integration_sdk.ui import Spinner
from vmware_aria_operations_integration_sdk.validation.describe_checks import (
    validate_describe,
)
from vmware_aria_operations_integration_sdk.validation.input_validators import (
    ChainValidator,
)
from vmware_aria_operations_integration_sdk.validation.input_validators import (
    IntegerValidator,
)
from vmware_aria_operations_integration_sdk.validation.input_validators import (
    NotEmptyValidator,
)
from vmware_aria_operations_integration_sdk.validation.input_validators import (
    TimeValidator,
)
from vmware_aria_operations_integration_sdk.validation.input_validators import (
    UniquenessValidator,
)
from vmware_aria_operations_integration_sdk.validation.result import Result

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)
console_handler = PTKHandler()
console_handler.setFormatter(CustomFormatter())
console_handler.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
logger.addHandler(console_handler)


async def run_long_collect(
    timeout: Optional[float],
    project: Project,
    connection: Connection,
    adapter_container: AdapterContainer,
    **kwargs: Any,
) -> LongCollectionBundle:
    logger.debug("Starting long run")
    cli_args = kwargs.get("cli_args", {})

    duration = cli_args.get("duration", None) or prompt(
        message="Collection duration: ",
        default="6h",
        validator=TimeValidator("Long run duration"),
        description="The long run duration is the total period of time for the long collection. Defaults to "
        "6 hours. Allowable units are s (seconds), m (minutes, default), and h (hours).",
    )
    collection_interval = cli_args.get("collection_interval", None) or prompt(
        message="Collection interval: ",
        default="5m",
        validator=TimeValidator("Collection interval"),
        description="The collection interval is the period of time between a collection starting and the next "
        "collection starting. Defaults to 5 minutes. Allowable units are s (seconds), m (minutes, "
        "default), and h (hours). By default, the timeout is set to 1.5 times the collection "
        "interval. If a collection takes longer than the interval, the next collection will start "
        "as soon as the the current one finishes.",
    )

    duration = TimeValidator.get_sec("Long run duration", duration)
    collection_interval = TimeValidator.get_sec(
        "Collection interval", collection_interval
    )

    if timeout is None:
        timeout = 1.5 * collection_interval

    if duration < collection_interval:
        times = 1
    else:
        # Remove decimal points by casting number to integer, which behaves as a floor function
        times = int(duration / collection_interval)

    # Wait for the container to finish starting *after* we've read in all the user input.
    await adapter_container.wait_for_container_startup()

    long_collection_bundle = LongCollectionBundle(collection_interval, duration)
    for collection_no in range(1, times + 1):
        title = f"Running collection No. {collection_no} of {times}"
        collection_bundle = await run_collect(
            timeout, project, connection, adapter_container, title=title
        )
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


async def run_collect(
    timeout: Optional[float],
    project: Project,
    connection: Connection,
    adapter_container: AdapterContainer,
    title: str = "Running Collect",
    **kwargs: Any,
) -> CollectionBundle:
    if timeout is None:
        timeout = TimeValidator.get_sec("Collection Timeout", "5m")

    cli_args = kwargs.get("cli_args", {})
    collection_number = cli_args.get("collection_number", None)
    collection_window = None
    if cli_args.get("collection_window_duration", None):
        duration = TimeValidator.get_sec(
            "Collection Window Duration",
            cli_args.get("collection_window_duration", "5m"),
        )
        end = time.time()
        collection_window = {
            "startTime": (end - duration) * 1000,
            "endTime": end * 1000,
        }
    connection.custom_collection_number = collection_number
    connection.custom_collection_window = collection_window

    await adapter_container.wait_for_container_startup()
    with Spinner(title):
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with await adapter_container.record_stats():
                request, response, elapsed_time = await send_post_to_adapter(
                    client, project, connection, COLLECT_ENDPOINT
                )
            return CollectionBundle(
                request, response, elapsed_time, adapter_container.stats
            )


async def run_connect(
    timeout: Optional[float],
    project: Project,
    connection: Connection,
    adapter_container: AdapterContainer,
    title: str = "Running Connect",
    **kwargs: Any,
) -> ConnectBundle:
    if timeout is None:
        timeout = TimeValidator.get_sec("Connection Timeout", "30s")
    await adapter_container.wait_for_container_startup()
    with Spinner(title):
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with await adapter_container.record_stats():
                request, response, elapsed_time = await send_post_to_adapter(
                    client, project, connection, CONNECT_ENDPOINT
                )
            return ConnectBundle(
                request, response, elapsed_time, adapter_container.stats
            )


async def run_get_endpoint_urls(
    timeout: Optional[float],
    project: Project,
    connection: Connection,
    adapter_container: AdapterContainer,
    title: str = "Running Endpoint URLs",
    **kwargs: Any,
) -> EndpointURLsBundle:
    if timeout is None:
        timeout = TimeValidator.get_sec("Connection Timeout", "30s")
    await adapter_container.wait_for_container_startup()
    with Spinner(title):
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with await adapter_container.record_stats():
                request, response, elapsed_time = await send_post_to_adapter(
                    client, project, connection, ENDPOINTS_URLS_ENDPOINT
                )
            return EndpointURLsBundle(
                request, response, elapsed_time, adapter_container.stats
            )


async def run_get_adapter_definition(
    timeout: Optional[float],
    project: Project,
    connection: Connection,
    adapter_container: AdapterContainer,
    title: str = "Running Adapter Definition",
    **kwargs: Any,
) -> AdapterDefinitionBundle:
    if timeout is None:
        timeout = TimeValidator.get_sec("Connection Timeout", "30s")
    await adapter_container.wait_for_container_startup()
    with Spinner(title):
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with await adapter_container.record_stats():
                request, response, elapsed_time = await send_get_to_adapter(
                    client, adapter_container.exposed_port, ADAPTER_DEFINITION_ENDPOINT
                )
            return AdapterDefinitionBundle(
                request, response, elapsed_time, adapter_container.stats
            )


async def run_get_server_version(
    timeout: Optional[float],
    adapter_container: AdapterContainer,
    title: str = "Running Get API " "Version",
    **kwargs: Any,
) -> VersionBundle:
    if timeout is None:
        timeout = TimeValidator.get_sec("Connection Timeout", "30s")
    await adapter_container.wait_for_container_startup()
    with Spinner(title):
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with await adapter_container.record_stats():
                request, response, elapsed_time = await send_get_to_adapter(
                    client, adapter_container.exposed_port, API_VERSION_ENDPOINT
                )
            return VersionBundle(
                request, response, elapsed_time, adapter_container.stats
            )


async def run_wait(adapter_container: AdapterContainer, **kwargs: Any) -> WaitBundle:
    await adapter_container.wait_for_container_startup()
    start_time = time.perf_counter()
    async with await adapter_container.record_stats():
        prompt("Press enter to stop container and exit.")
    return WaitBundle(time.perf_counter() - start_time, adapter_container.stats)


async def run(arguments: Any) -> None:
    # User input
    project = get_project(arguments)

    # start to get/build container image as soon as possible, which requires project
    # get_container_image is threaded, so it can build in the background. If the user
    # didn't specify all parameters on the command line and there are interactive
    # prompts, this can provide a noticeable speed increase.
    adapter_container = AdapterContainer(project.path)
    adapter_container.exposed_port = project.port
    Describe.initialize(project.path, adapter_container)

    # Set up logger, which requires project
    log_file_path = os.path.join(project.path, "logs")
    if not os.path.exists(log_file_path):
        mkdir(log_file_path)

    try:
        log_handler = RotatingFileHandler(
            os.path.join(log_file_path, "test.log"),
            # No max size, but we'll roll over immediately so each test has its own file
            maxBytes=0,
            backupCount=5,
        )
        logging.basicConfig(
            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
            datefmt="%H:%M:%S",
            handlers=[log_handler],
            level=logging.DEBUG,
        )
        log_handler.doRollover()
    except Exception as e:
        logger.warning(f"Unable to save logs to {log_file_path}: {e}")

    connection = await get_connection(project, adapter_container, arguments)

    try:
        adapter_container.memory_limit = connection.get_memory_limit()
        adapter_container.start()
        # Get the method to test
        method = get_method(arguments)
        verbosity = arguments.verbosity

        # Get certificates and add to connection if we are running any of the test or collect methods
        # We will distinguish between 'None' (endpointURLs has not been called) and '[]' (endpointURLs has been
        # called but no certificates were found).
        if (
            method in [run_connect, run_collect, run_long_collect]
            and connection.certificates is None
        ):
            try:
                endpoints = await run_get_endpoint_urls(
                    30, project, connection, adapter_container
                )
                certificates = endpoints.retrieve_certificates()
                connection.certificates = certificates
                # Record certificates in connection to omit this step next time.
                # Certificates can be regenerated by removing the 'certificates' key
                # from the connection.
                project.record()
            except Exception as e:
                logger.warning(
                    f"Caught exception when retrieving SSL certificates: {e}."
                )
        if connection.certificates is None:
            logger.warning(
                f"Error retrieving SSL certificates from 'endpointURLs'. "
                f"Proceeding without certificates."
            )

        # async event loop
        args = vars(arguments)
        timeout = args.get("timeout", None)
        if timeout is not None:
            timeout = TimeValidator.get_sec("Timeout", timeout)

        result_bundle = await method(
            timeout=timeout,
            adapter_container=adapter_container,
            project=project,
            connection=connection,
            verbosity=verbosity,
            cli_args=vars(arguments),
        )
    finally:
        await adapter_container.stop()

    # TODO: Add UI code here
    # calculate_stats() ->all stats_object
    logger.info(result_bundle)
    display_ui(
        result_bundle.validate(project),
        os.path.join(project.path, "logs", "validation.log"),
        verbosity,
        type(result_bundle) is LongCollectionBundle,
    )


def get_method(arguments: Any) -> Callable:
    if "func" in vars(arguments):
        return vars(arguments)["func"]  # type: ignore

    return selection_prompt(  # type: ignore
        "Choose a method to test:",
        [
            (run_connect, "Test Connection"),
            (run_collect, "Collect"),
            (run_long_collect, "Long Run Collection"),
            (run_get_endpoint_urls, "Endpoint URLs"),
            (run_get_adapter_definition, "Adapter Definition"),
            (run_get_server_version, "Version"),
        ],
    )


# TODO: move this to UI
def display_ui(
    result: Result,
    validation_file_path: str,
    verbosity: int,
    over_write_minimum_log_level: bool,
) -> None:
    if over_write_minimum_log_level and verbosity < 2:
        verbosity = 2

    for severity, message in result.messages:
        if severity.value <= verbosity:
            if severity.value == 1:
                logger.error(message)
            elif severity.value == 2:
                logger.warning(message)
            else:
                logger.info(message)
    write_validation_log(validation_file_path, result)

    if len(result.messages) > 0:
        logger.info(f"All validation logs written to '{validation_file_path}'")
    if result.error_count > 0 and verbosity < 1:
        logger.error(f"Found {result.error_count} errors when validating response")
    if result.warning_count > 0 and verbosity < 2:
        logger.warning(
            f"Found {result.warning_count} warnings when validating response"
        )

    if result.error_count + result.warning_count == 0:
        logger.info(
            "Validation passed with no errors", extra={"style": "class:success"}
        )


# TODO: a new file inside of the validation module
def write_validation_log(validation_file_path: str, result: Result) -> None:
    # TODO: create a test object to be able to write encapsulated test results
    with open(validation_file_path, "w") as validation_file:
        for severity, message in result.messages:
            validation_file.write(f"{severity.name}: {message}\n")


# Helpers for creating the json payload ***************


async def get_connection(
    project: Project, adapter_container: AdapterContainer, arguments: Any
) -> Connection:
    connection_names = [
        (connection.name, connection.name) for connection in project.connections
    ]

    if (arguments.connection, arguments.connection) not in connection_names:
        connection_name = selection_prompt(
            "Choose a connection: ",
            connection_names + [("new_connection", "New Connection")],
        )
    else:
        connection_name = arguments.connection

    if connection_name != "new_connection":
        for connection in project.connections:
            if connection.name == connection_name:
                return connection
        logger.error(f"Cannot find connection with name '{connection_name}'.")
        exit(1)

    # We should ensure the 'describe' file is valid before parsing through it.
    describe, resources = await Describe.get(project.port)
    validate_describe(project.path, describe)
    adapter_instance_kind = get_adapter_instance(describe)
    if adapter_instance_kind is None:
        logger.error("Cannot find adapter instance in conf/describe.xml.")
        logger.error(
            "Make sure the adapter instance resource kind exists and has tag 'type=\"7\"'."
        )
        exit(1)

    print_formatted(
        """Connections are akin to Adapter Instances in VMware Aria Operations, and contain the parameters 
needed to connect to a target environment. As such, the following connection parameters and credential fields are 
derived from the 'conf/describe.xml' file and are specific to each Management Pack.""",
        "class:information",
        frame=True,
    )

    identifiers = {}
    for identifier in sorted(
        get_identifiers(adapter_instance_kind),
        key=lambda i: int(i.get("dispOrder") or "100"),
    ):
        value = input_parameter("connection parameter", identifier, resources)

        identifiers[identifier.get("key")] = {
            "value": value,
            "required": is_true(identifier, "required", default="true"),
            "part_of_uniqueness": identifier.get("identType", "1") == "1",
        }

    valid_credential_kind_keys = (
        adapter_instance_kind.get("credentialKind") or ""
    ).split(",")
    credential_kinds = {
        credential_kind.get("key"): credential_kind
        for credential_kind in get_credential_kinds(describe)
        if credential_kind.get("key") in valid_credential_kind_keys
    }

    credential_type = valid_credential_kind_keys[0]

    if len(valid_credential_kind_keys) > 1:
        credential_type = selection_prompt(
            "Select the credential kind for this connection: ",
            [
                (kind.get("key"), resources.get(kind.get("nameKey"), kind.get("key")))
                for kind in list(credential_kinds.values())
            ],
        )

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
                "password": is_true(credential_field, "password"),
            }

    suite_api_credentials = get_suite_api_connection_info(project)

    existing_connection_names = [
        connection.name for connection in (project.connections or [])
    ]
    existing_connection_names.append("New Connection")

    name = prompt(
        message="Enter a name for this connection: ",
        validator=UniquenessValidator("Connection name", existing_connection_names),
        validate_while_typing=False,
        description="The connection name is used to identify this connection (parameters and credential) in\n"
        "command line arguments or in the interactive prompt.",
    )
    new_connection = Connection(
        name, identifiers, credentials, None, suite_api_credentials
    )
    project.connections.append(new_connection)
    record_project(project)
    print_formatted(
        f"Saved connection '{name}' in '{os.path.join(project.path, 'config.json')}'.",
        "class:success",
    )
    print_formatted(
        f"The connection can be modified by manually editing this file.",
        "class:success",
    )
    return new_connection


def get_suite_api_connection_info(project: Project) -> Tuple[str, str, str]:
    suiteapi_hostname = get_config_value(
        CONFIG_SUITE_API_HOSTNAME_KEY,
        "hostname",
        os.path.join(project.path, "config.json"),
    )
    suiteapi_username = get_config_value(
        CONFIG_SUITE_API_USERNAME_KEY,
        "username",
        os.path.join(project.path, "config.json"),
    )
    suiteapi_password = get_config_value(
        CONFIG_SUITE_API_PASSWORD_KEY,
        "password",
        os.path.join(project.path, "config.json"),
    )
    has_default = False if suiteapi_hostname == "hostname" else True
    suite_api_prompt = "Set connection information for SuiteAPI calls? "
    description = ""
    if has_default:
        suite_api_prompt = (
            "Override default SuiteAPI connection information for SuiteAPI calls? "
        )
        description = f"Default SuiteAPI host/user is currently: '{suiteapi_hostname}'/'{suiteapi_username}'."
    suite_api_response = selection_prompt(
        suite_api_prompt, [("yes", "Yes"), ("no", "No")], description
    )
    if suite_api_response == "yes":
        suiteapi_hostname = prompt("Suite API Hostname: ")
        suiteapi_username = prompt("Suite API User Name: ")
        suiteapi_password = prompt("Suite API Password: ", is_password=True)
        if not has_default:
            description = "Default SuiteAPI host/user is not currently set."
        if (
            selection_prompt(
                "Set these as the default SuiteAPI connection? ",
                [("yes", "Yes"), ("no", "No")],
                description,
            )
            == "yes"
        ):
            set_config_value(
                CONFIG_SUITE_API_HOSTNAME_KEY,
                suiteapi_hostname,
                os.path.join(project.path, "config.json"),
            )
            set_config_value(
                CONFIG_SUITE_API_USERNAME_KEY,
                suiteapi_username,
                os.path.join(project.path, "config.json"),
            )
            set_config_value(
                CONFIG_SUITE_API_PASSWORD_KEY,
                suiteapi_password,
                os.path.join(project.path, "config.json"),
            )
    else:
        suiteapi_hostname = None
        suiteapi_username = None
        suiteapi_password = None

    return suiteapi_hostname, suiteapi_username, suiteapi_password


def input_parameter(parameter_type: str, parameter: Element, resources: Dict) -> str:
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
        enum_values = [
            (
                enum_value.get("value"),
                resources.get(enum_value.get("nameKey"), enum_value.get("value")),
            )
            for enum_value in parameter.findall(ns("enum"))
        ]
        value = selection_prompt(
            f"Enter {parameter_type} '{label}'{postfix}", enum_values, description
        )
    else:
        value = prompt(
            message=f"Enter {parameter_type} '{label}'{postfix}",
            default=default,
            is_password=is_password,
            validator=ChainValidator(
                [
                    ConditionalValidator(
                        NotEmptyValidator(f"{parameter_type.capitalize()} '{label}'"),
                        is_required,
                    ),
                    ConditionalValidator(
                        IntegerValidator(f"{parameter_type.capitalize()} '{label}'"),
                        is_integer,
                    ),
                ]
            ),
            description=description,
        )
    return value  # type: ignore


def main() -> None:
    description = "Tool for running adapter test and collect methods outside of a VMware Aria Operations Cloud Proxy."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=pkg_resources.get_distribution(
            "vmware-aria-operations-integration-sdk"
        ).version,
    )

    # General options
    parser.add_argument(
        "-p",
        "--path",
        help="Path to root directory of project. Defaults to the current directory, "
        "or prompts if current directory is not a project.",
    )
    parser.add_argument(
        "-c", "--connection", help="Name of a connection in this project."
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        help="Determine the amount of console logging when performing validation. "
        "0: No console logging; 3: Max console logging.",
        type=int,
        default=1,
        choices=range(0, 4),
        metavar="[0-3]",
    )

    methods = parser.add_subparsers(required=False)

    # Test method
    test_method = methods.add_parser(
        "connect",
        help="Simulate the 'test connection' method being called by the VMware Aria Operations collector.",
    )
    test_method.set_defaults(func=run_connect)
    test_method.add_argument(
        "-t",
        "--timeout",
        help="Timeout limit for REST request performed.",
        type=str,
        default="30s",
    )

    # Collect method
    collect_method = methods.add_parser(
        "collect",
        help="Simulate the 'collect' method being called by the VMware Aria Operations collector.",
    )
    collect_method.set_defaults(func=run_collect)
    collect_method.add_argument(
        "-n",
        "--collection-number",
        help="Start at a custom collection number instead of 0.",
        type=int,
        default=0,
        choices=range(0, 1000),
        metavar="[0-999]",
    )
    collect_method.add_argument(
        "-w",
        "--collection-window-duration",
        help="Sets a custom collection window duration in h hours, m minutes, or s "
        "seconds. The collection window end time will always be the current time. For "
        "example, '-w 20m' sets the window to the interval (20 minutes before now, now).",
        type=str,
        default="",
    )
    collect_method.add_argument(
        "-t",
        "--timeout",
        help="Timeout limit for REST request performed.",
        type=str,
        default="5m",
    )

    # Long run method
    long_run_method = methods.add_parser(
        "long-run",
        help="Simulate a long run collection and return data statistics about the "
        "overall collection.",
    )
    long_run_method.set_defaults(func=run_long_collect)

    long_run_method.add_argument(
        "-d",
        "--duration",
        help="Duration of the long run in h hours, m minutes, or s seconds.",
        type=str,
        default="6h",
    )

    long_run_method.add_argument(
        "-i",
        "--collection-interval",
        help="Amount of time to wait between collection start times. If a collection "
        "surpasses this interval, the next collection is delayed.",
        type=str,
        default="5m",
    )

    long_run_method.add_argument(
        "-t",
        "--timeout",
        help="Timeout limit for REST request performed. By default, the timeout will be set "
        "to 1.5 times the duration of the collection interval.",
        type=str,
    )

    # URL Endpoints method
    url_method = methods.add_parser(
        "endpoint_urls",
        help="Simulate the 'endpoint_urls' method being called by the VMware Aria Operations collector.",
    )
    url_method.set_defaults(func=run_get_endpoint_urls)
    url_method.add_argument(
        "-t",
        "--timeout",
        help="Timeout limit for REST request performed.",
        type=str,
        default="30s",
    )

    # URL Endpoints method
    url_method = methods.add_parser(
        "adapter_definition",
        help="Simulate the 'adapterDefinition' method being called by the mp-build tool to generate a describe.xml file.",
    )
    url_method.set_defaults(func=run_get_adapter_definition)
    url_method.add_argument(
        "-t",
        "--timeout",
        help="Timeout limit for REST request performed.",
        type=str,
        default="30s",
    )

    # Version method
    version_method = methods.add_parser(
        "version",
        help="Simulate the 'version' method being called by the VMware Aria Operations collector.",
    )
    version_method.set_defaults(func=run_get_server_version)
    version_method.add_argument(
        "-t",
        "--timeout",
        help="Timeout limit for REST request performed.",
        type=str,
        default="30s",
    )

    # wait
    wait_method = methods.add_parser(
        "wait",
        help="Simulate the adapter running on a VMware Aria Operations collector and wait for user input "
        "to stop. Useful for calling REST methods via an external tool, such as "
        "Insomnia or Postman.",
    )
    wait_method.set_defaults(func=run_wait)

    try:
        asyncio.run(run(parser.parse_args()))
    except KeyboardInterrupt:
        logger.debug("Ctrl C pressed by user")
        print_formatted("")
        logger.info("Testing cancelled")
        exit(1)
    except ValidationError as validation_error:
        logger.error(validation_error.message)
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
        exit(1)
    except SystemExit as system_exit:
        exit(system_exit.code)
    except XMLSchemaValidationError as xml_error:
        logger.error(xml_error)
        logger.error("Fix describe.xml before proceeding")
        exit(1)
    except BaseException as base_error:
        print_formatted("Unexpected error")
        logger.error(base_error)
        traceback.print_tb(base_error.__traceback__)
        exit(1)


if __name__ == "__main__":
    main()
