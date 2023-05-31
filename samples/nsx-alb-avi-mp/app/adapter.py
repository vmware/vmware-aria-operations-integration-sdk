#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import sys
from typing import List

import aria.ops.adapter_logging as logging
import constants
from aria.ops.adapter_instance import AdapterInstance
from aria.ops.definition.adapter_definition import AdapterDefinition
from aria.ops.definition.units import Units
from aria.ops.result import CollectResult
from aria.ops.result import EndpointResult
from aria.ops.result import TestResult
from aria.ops.timer import Timer
from avi.sdk.avi_api import ApiSession
from cloud import add_cloud_children
from cloud import get_clouds
from service_engine import get_service_engines
from service_engine_groups import add_service_engine_group_children
from service_engine_groups import get_service_engine_groups
from tenant import add_tenant_children
from tenant import get_tenants
from virtual_service import add_virtual_services_children
from virtual_service import get_virtual_services

""" A reference to the logger, which is configured in the main method.
Using __name__ instead of the current file name allows us to refactor the code in the future without having to do
a more significant refactoring
"""
logger = logging.getLogger(__name__)


def get_adapter_definition() -> AdapterDefinition:
    with Timer(logger, "Adapter Definition"):
        definition = AdapterDefinition(
            "NSXALBAdapter",
            "NSX ALB (Avi)",
            "nsx_alb_adapter_instance",
            "NSX ALB Adapter Instance",
        )

        definition.define_string_parameter("host", "Host")
        definition.define_int_parameter("timeout", "Connection Timeout (s)", default=5)

        credential = definition.define_credential_type(
            "nsx_alb_credentials", "NSX ALB Credential"
        )
        credential.define_string_parameter("username", "Username")
        credential.define_password_parameter("password", "Password")

        tenant = definition.define_object_type("tenant", "Tenant")
        tenant.define_string_identifier("uuid", "UUID")
        tenant.define_metric("virtual_services", "Virtual Services")
        tenant.define_metric("clouds", "Clouds")

        cloud = definition.define_object_type("cloud", "Cloud")
        cloud.define_string_identifier("uuid", "UUID")
        cloud.define_string_property("license_type", "License Type")
        cloud.define_metric("virtual_services", "Virtual Services")

        service_engine_group = definition.define_object_type(
            "service_engine_group", "Service Engine Group"
        )
        service_engine_group.define_string_identifier("uuid", "UUID")
        service_engine_group.define_string_property("license_type", "License Type")
        service_engine_group.define_metric("service_engines", "Service Engines")

        service_engine = definition.define_object_type(
            "service_engine", "Service Engine"
        )
        service_engine.define_string_identifier("uuid", "UUID")
        service_engine.define_string_property("controller_ip", "Controller IP Address")
        service_engine.define_metric(
            "total_cpu_utilization", "CPU Utilization", unit=Units.RATIO.PERCENT
        )
        service_engine.define_metric(
            "total_memory", "Memory Capacity", unit=Units.DATA_SIZE.BYTE
        )
        service_engine.define_metric(
            "free_memory", "Memory Free", unit=Units.DATA_SIZE.BYTE
        )

        virtual_service = definition.define_object_type(
            "virtual_service", "Virtual Service"
        )
        virtual_service.define_string_identifier("uuid", "UUID")
        virtual_service.define_string_property("cloud_ref", "Parent Cloud")
        virtual_service.define_string_property("se_uuid", "Parent Service Engine")
        virtual_service.define_metric(
            "total_packets_received", "Total Packets Received"
        )
        virtual_service.define_metric(
            "data_received", "Data Received", unit=Units.DATA_SIZE.BYTE
        )
        virtual_service.define_metric("total_packets_sent", "Total Packets Sent")
        virtual_service.define_metric(
            "data_sent", "Data Sent", unit=Units.DATA_SIZE.BYTE
        )

        return definition


def test(adapter_instance: AdapterInstance) -> TestResult:
    """Runs a connection test to ensure the adapter is able to establish a connection with the host

    This is a good place to establish a connection, check user privileges, and other checks.
    However, it is generally not necessary to check every single endpoint the MP uses to run a collection, as this may cause
    performance issues and unnecessary overhead.

    :return: A TestResult Object an errorMessage in the case of a failure
    """
    with Timer(logger, "Test"):
        result = TestResult()

        try:
            connect(adapter_instance)
        except ConnectionError as connection_error:
            result.with_error(f"Connection error: {connection_error.args}")
        except Exception as unexpected_error:
            result.with_error(f"Unexpected API error: {unexpected_error.args}")
        finally:
            return result


def connect(adapter_instance: AdapterInstance) -> ApiSession:
    """Establishes a connection with the host

    :return: ApiSession an AVI session object
    :except: KeyError environment variable is not found
    """
    with Timer(logger, "Get Session"):
        controller = adapter_instance.get_identifier_value("host")
        timeout = int(adapter_instance.get_identifier_value("timeout"))

        if controller is None:
            raise ConnectionError("No host provided")
        if "username" not in adapter_instance.credentials:
            raise ConnectionError("No username provided")
        if "password" not in adapter_instance.credentials:
            raise ConnectionError("No password provided")

        # logs are stored in a log file in the Node running the Management pack
        logger.debug(f"Connecting to host: {controller}")

        return ApiSession.get_session(
            controller,
            username=adapter_instance.credentials["username"],
            password=adapter_instance.credentials["password"],
            tenant="admin",
            timeout=timeout,
            api_version=constants.AVI_API_VERSION,
            max_api_retries=5,
            retry_conxn_errors=False,
        )


def collect(adapter_instance: AdapterInstance) -> CollectResult:
    """Collects all defined metrics, adds resource children, and create events

    :return: A JSON object with the collection response, including any errors that occurred.
    """
    with Timer(logger, "Collect"):
        result = CollectResult()

        try:
            # Collect each resource type
            api = connect(adapter_instance)

            with Timer(logger, "Collect Objects"):
                tenants = get_tenants(api)
                clouds = get_clouds(api)
                service_engines = get_service_engines(api)
                service_engine_groups = get_service_engine_groups(api)
                virtual_services = get_virtual_services(api)

            # Add relationships to each parent resource
            with Timer(logger, "Add Relationships"):
                tenants = add_tenant_children(tenants, clouds)
                clouds = add_cloud_children(
                    clouds, service_engine_groups, virtual_services
                )
                service_engine_groups = add_service_engine_group_children(
                    service_engine_groups, service_engines
                )
                virtual_services = add_virtual_services_children(
                    virtual_services, service_engines
                )

            # Gather all resources in a single list
            result.add_objects(tenants)
            result.add_objects(clouds)
            result.add_objects(service_engines)
            result.add_objects(service_engine_groups)
            result.add_objects(virtual_services)

        except ConnectionError as connection_error:
            logger.error(f"Connection error during collection")
            logger.error(connection_error.args)
            result.with_error("Collection error: " + repr(connection_error))
        except Exception as e:
            # TODO: If any connections are still open, make sure they are closed before returning
            logger.error("Unexpected collection error")
            logger.exception(e)
            result.with_error("Unexpected collection error: " + repr(e))
        finally:
            return result


def get_endpoints(adapter_instance: AdapterInstance) -> EndpointResult:
    # In the case that an SSL Certificate is needed to communicate to the target,
    # add each URL that the adapter uses here. Often this will be derived from a 'host'
    # parameter in the adapter instance. In this Adapter we don't use any HTTPS
    # connections, so we won't add any. If we did, we might do something like this:
    # result.with_endpoint(adapter_instance.get_identifier_value("host"))
    #
    # Multiple endpoints can be returned, like this:
    # result.with_endpoint(adapter_instance.get_identifier_value("primary_host"))
    # result.with_endpoint(adapter_instance.get_identifier_value("secondary_host"))
    #
    # This 'get_endpoints' method will be run before the 'test' method,
    # and vROps will use the results to extract a certificate from each URL. If the
    # certificate is not trusted by the vROps Trust Store, the user will be prompted
    # to either accept or reject the certificate. If it is accepted, the certificate
    # will be added to the AdapterInstance object that is passed to the 'test' and
    # 'collect' methods. Any certificate that is encountered in those methods should
    # then be validated against the certificate(s) in the AdapterInstance.
    with Timer(logger, "Get endpoint URLs"):
        return EndpointResult()


def main(argv: List[str]) -> None:
    logging.setup_logging("adapter.log")
    # Start a new log file by calling 'rotate'. By default, the last five calls will be
    # retained. If the logs are not manually rotated, the 'setup_logging' call should be
    # invoked with the 'max_size' parameter set to a reasonable value, e.g.,
    # 10_489_760 (10MB).
    logging.rotate()
    logger.info(f"Running adapter code with arguments: {argv}")
    if len(argv) != 3:
        # `inputfile` and `outputfile` are always automatically appended to the
        # argument list by the server
        logger.debug("Arguments must be <method> <inputfile> <ouputfile>")
        exit(1)

    method = argv[0]

    try:
        if method == "test":
            test(AdapterInstance.from_input()).send_results()
        elif method == "endpoint_urls":
            get_endpoints(AdapterInstance.from_input()).send_results()
        elif method == "collect":
            collect(AdapterInstance.from_input()).send_results()
        elif method == "adapter_definition":
            result = get_adapter_definition()
            if type(result) is AdapterDefinition:
                result.send_results()
            else:
                logger.info(
                    "get_adapter_definition method did not return an AdapterDefinition"
                )
                exit(1)
        else:
            logger.debug(f"Command {method} not found")
            exit(1)
    finally:
        logger.info(Timer.graph())


if __name__ == "__main__":
    main(sys.argv[1:])
