#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import sys
from typing import List

import aria.ops.adapter_logging as logging
import requests as requests
from aria.ops.adapter_instance import AdapterInstance
from aria.ops.data import Metric
from aria.ops.data import Property
from aria.ops.definition.adapter_definition import AdapterDefinition
from aria.ops.definition.units import Units
from aria.ops.event import Criticality
from aria.ops.result import CollectResult
from aria.ops.result import EndpointResult
from aria.ops.result import TestResult
from aria.ops.timer import Timer
from constants import ADAPTER_KIND
from constants import ADAPTER_NAME

logger = logging.getLogger(__name__)


def get_adapter_definition() -> AdapterDefinition:
    """
    The adapter definition defines the object types and attribute types
    (metric/property) that are present in a collection. Setting these object types and
    attribute types helps VMware Aria Operations to validate, process, and display the
    data correctly.
    :return: AdapterDefinition
    """
    with Timer(logger, "Get Adapter Definition"):
        definition = AdapterDefinition(ADAPTER_KIND, ADAPTER_NAME)

        # TODO: Define necessary parameters. Host and Port are provided, as they are
        #       commonly used

        # The test and collect methods assume the host is a pypi server.
        definition.define_string_parameter(
            "host",
            label="Hostname",
            description="Hostname of the REST Server",
            default="pypi.org",
            required=True,
        )

        # This parameter is specific to the example collection
        definition.define_string_parameter(
            "project_names",
            label="Project Name(s)",
            description="A comma-separated list of projects",
            default="vmware-aria-operations-integration-sdk,vmware-aria-operations-integration-sdk-lib",
        )

        # Advanced parameters follow. These are not shown to the user by default.

        # TODO: Uncomment if needed, or delete
        # definition.define_int_parameter(
        #     "port",
        #     label="Port",
        #     description="Port for the REST Server",
        #     required=False,
        #     advanced=True,
        #     default=443,
        # )

        # The key 'container_memory_limit' is a special key that is read by the VMware
        # Aria Operations collector to determine how much memory to allocate to the
        # Docker container running this adapter. It does not need to be read inside the
        # adapter code. However, removing the definition from the object model will
        # remove the ability to change the container memory limit during the adapter's
        # configuration, and the VMware Aria Operations collector will give 1024 MB of
        # memory to the container running the adapter instance.
        definition.define_int_parameter(
            "container_memory_limit",
            label="Adapter Memory Limit (MB)",
            description="Sets the maximum amount of memory VMware Aria Operations can "
            "allocate to the container running this adapter instance.",
            required=True,
            advanced=True,
            default=1024,
        )

        # TODO: Add a credential if necessary. Examples:
        # basic = definition.define_credential_type("basic_auth", "Basic Auth")
        # basic.define_string_parameter("user", "Username")
        # basic.define_password_parameter("password", "Password")
        #
        # token = definition.define_credential_type("token_auth", "Token Auth")
        # token.define_password_parameter("token", "Token")

        # Note: OAuth and OAuth2 are complex and implementation will be somewhat
        # dependent on the details of the specific API. The 'requests-oauthlib' library
        # works will with the requests

        # TODO: Add object types, properties, and metrics
        project = definition.define_object_type("project", "Python Project")
        project.define_string_property("summary", "Summary")
        project.define_string_property("version", "Current Version")
        project.define_metric("vulnerability_count", "Number of Vulnerabilities")

        logger.debug(f"Returning adapter definition: {definition.to_json()}")
        return definition


def get_host(adapter_instance: AdapterInstance) -> str:
    """
    Helper method that gets the host and prepends the https protocol to the host if
    the protocol is not present
    :param adapter_instance: Adapter Instance object that holds the configuration
    :return: The host, including the protocol
    """
    host = adapter_instance.get_identifier_value("host")
    if host.startswith("http"):
        return str(host)
    else:
        return f"https://{host}"


def get_projects(adapter_instance: AdapterInstance) -> list[str]:
    """
    Helper method that gets the comma-separated project names and parses them into a
    list.
    :param adapter_instance: Adapter Instance object that holds the configuration
    :return: A list of project names
    """
    projects = adapter_instance.get_identifier_value("project_names")
    if not projects:
        return []
    return [project.strip() for project in projects.split(",")]


def test(adapter_instance: AdapterInstance) -> TestResult:
    with Timer(logger, "Test"):
        result = TestResult()
        try:
            # Sample test connection code follows. Replace with your own test connection
            # code. A typical test connection will generally consist of:
            # 1. Read identifier values from adapter_instance that are required to
            #    connect to the target(s)
            # 2. Connect to the target(s), and retrieve some sample data
            # 3. Disconnect cleanly from the target (ensure this happens even if an
            #    error occurs)
            # 4. If any of the above failed, return an error, otherwise pass.

            host = get_host(adapter_instance)
            if not host:
                result.with_error("No Host Found")

            # Example getting the port:
            # Port is optional, so we supply a default of 443.
            # port = int(adapter_instance.get_identifier_value("port", "443"))

            projects = get_projects(adapter_instance)
            if not projects:
                result.with_error("No project(s) found")

            # TODO: Authenticate if necessary and perform a request. Examples:
            # # Basic Authorization:
            # if adapter_instance.credential_type == "basic_auth":
            #     user = adapter_instance.get_credential_value("user")
            #     password = adapter_instance.get_credential_value("password")
            #     r = requests.get(f"{host}:{port}/{endpoint}", auth=(user, password))
            #
            # # API Key:
            # if adapter_instance.credential_type == "token_auth":
            #     token = adapter_instance.get_credential_value("token")
            #     r = requests.get(f"{host}:{port}/{endpoint}", headers={"token", token})

            for project in projects:
                # The 'requests' library is simple but powerful.
                # See https://requests.readthedocs.io/en/latest/user/quickstart/ for
                # documentation.

                # No credential required for this API
                r = requests.get(f"{host}/pypi/{project}/json")

                if r.status_code > 299:
                    result.with_error(f"Unsuccessful request: {r}")
                else:
                    logger.debug(r.json())

        except Exception as e:
            logger.error("Unexpected connection test error")
            logger.exception(e)
            result.with_error("Unexpected connection test error: " + repr(e))
        finally:
            # TODO: If any connections are still open, make sure they are closed before
            #  returning
            logger.debug(f"Returning test result: {result.get_json()}")
            return result


def collect(adapter_instance: AdapterInstance) -> CollectResult:
    with Timer(logger, "Collection"):
        result = CollectResult()
        try:
            # Sample collection code follows. Replace this with your own collection
            # code. A typical collection will generally consist of:
            # 1. Read identifier values from adapter_instance that are required to
            #    connect to the target(s)
            # 2. Connect to the target(s), and retrieve data
            # 3. Add the data into a CollectResult's objects, properties, metrics, etc
            # 4. Disconnect cleanly from the target (ensure this happens even if an
            #    error occurs)
            # 5. Return the CollectResult.
            host = get_host(adapter_instance)
            projects = get_projects(adapter_instance)

            # Because we are supplying the host to `get_endpoints` (see method below),
            # the certificate is passed to the test and collect methods inside the
            # AdapterInstance object. To verify each request against this certificate,
            # see https://www.misterpki.com/python-requests-authentication/
            # If you do not want to verify the certificate, you can remove the host from
            # the 'get_endpoints' method, and pass the "verify=False" argument to each
            # request.

            if not host:
                result.with_error("No Host Found")
            if not projects:
                result.with_error("No project(s) found")

            for project in projects:
                # No credential required for this API:
                r = requests.get(f"{host}/pypi/{project}/json")

                # all codes in the 200 range indicate success.
                if r.status_code > 299:
                    result.with_error(
                        f"Unsuccessful request for project {project}: {r}"
                    )
                else:
                    project_info = r.json()
                    logger.debug(project_info)
                    project_obj = result.object(ADAPTER_KIND, "project", project)
                    project_obj.with_property(
                        "summary", project_info.get("info").get("summary")
                    )
                    project_obj.with_property(
                        "version", project_info.get("info").get("version")
                    )
                    project_obj.with_metric(
                        "vulnerability_count", len(project_info.get("vulnerabilities"))
                    )

                    for vulnerability in project_info.get("vulnerabilities"):
                        if vulnerability.get("withdrawn") is not None:
                            continue
                        project_obj.with_event(
                            message=f"{vulnerability.get('id')}\n\n{vulnerability.get('details')}\n\nFor more information see {vulnerability.get('link')}",
                            criticality=Criticality.CRITICAL,
                        )

        except Exception as e:
            logger.error("Unexpected collection error")
            logger.exception(e)
            result.with_error("Unexpected collection error: " + repr(e))
        finally:
            # TODO: If any connections are still open, make sure they are closed before
            #  returning
            logger.debug(f"Returning collection result {result.get_json()}")
            return result


def get_endpoints(adapter_instance: AdapterInstance) -> EndpointResult:
    with Timer(logger, "Get Endpoints"):
        result = EndpointResult()
        # In the case that an SSL Certificate is needed to communicate to the target,
        # add each URL that the adapter uses here. Often this will be derived from a
        # 'host' parameter in the adapter instance. In this Adapter we don't use any
        # HTTPS connections, so we won't add any. If we did, we might do something like
        # this:
        # result.with_endpoint(adapter_instance.get_identifier_value("host"))
        #
        # Multiple endpoints can be returned, like this:
        # result.with_endpoint(adapter_instance.get_identifier_value("primary_host"))
        # result.with_endpoint(adapter_instance.get_identifier_value("secondary_host"))
        #
        # This 'get_endpoints' method will be run before the 'test' method,
        # and VMware Aria Operations will use the results to extract a certificate from
        # each URL. If the certificate is not trusted by the VMware Aria Operations
        # Trust Store, the user will be prompted to either accept or reject the
        # certificate. If it is accepted, the certificate will be added to the
        # AdapterInstance object that is passed to the 'test' and 'collect' methods.
        # Any certificate that is encountered in those methods should then be validated
        # against the certificate(s) in the AdapterInstance.

        # The protocol is required. We'll use a helper method (get_host) to ensure it is
        # present
        result.with_endpoint(get_host(adapter_instance))

        logger.debug(f"Returning endpoints: {result.get_json()}")
        return result


# Main entry point of the adapter. You should not need to modify anything below this line.
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
        logger.error("Arguments must be <method> <inputfile> <ouputfile>")
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
            logger.error(f"Command {method} not found")
            exit(1)
    finally:
        logger.info(Timer.graph())


if __name__ == "__main__":
    main(sys.argv[1:])
