#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import sys
from typing import List

import aria.ops.adapter_logging as logging
import psutil
from aria.ops.adapter_instance import AdapterInstance
from aria.ops.data import Metric
from aria.ops.data import Property
from aria.ops.definition.adapter_definition import AdapterDefinition
from aria.ops.definition.units import Units
from aria.ops.result import CollectResult
from aria.ops.result import EndpointResult
from aria.ops.result import TestResult
from aria.ops.timer import Timer
from constants import ADAPTER_KIND
from constants import ADAPTER_NAME

logger = logging.getLogger(__name__)


def get_adapter_definition() -> AdapterDefinition:
    """
    The adapter definition defines the object types and attribute types (metric/property) that are present
    in a collection. Setting these object types and attribute types helps VMware Aria Operations to
    validate, process, and display the data correctly.
    :return: AdapterDefinition
    """
    with Timer(logger, "Get Adapter Definition"):
        definition = AdapterDefinition(ADAPTER_KIND, ADAPTER_NAME)

        definition.define_string_parameter(
            "ID",
            label="ID",
            description="Example identifier. Using a value of 'bad' will cause "
            "test connection to fail; any other value will pass.",
            required=True,
        )
        # The key 'container_memory_limit' is a special key that is read by the VMware Aria Operations collector to
        # determine how much memory to allocate to the docker container running this adapter. It does not
        # need to be read inside the adapter code.
        definition.define_int_parameter(
            "container_memory_limit",
            label="Adapter Memory Limit (MB)",
            description="Sets the maximum amount of memory VMware Aria Operations can "
            "allocate to the container running this adapter instance.",
            required=True,
            advanced=True,
            default=1024,
        )

        cpu = definition.define_object_type("cpu", "CPU")
        cpu.define_numeric_property("cpu_count", "CPU Count", is_discrete=True)
        cpu.define_metric("user_time", "User Time", Units.TIME.SECONDS)
        cpu.define_metric(
            "nice_time", "Nice Time", Units.TIME.SECONDS, is_key_attribute=True
        )
        cpu.define_metric("system_time", "System Time", Units.TIME.SECONDS)
        cpu.define_metric("idle_time", "Idle Time", Units.TIME.SECONDS)

        disk = definition.define_object_type("disk", "Disk")
        disk.define_string_property("partition", "Partition")
        disk.define_metric(
            "total_space", "Total Space", is_discrete=True, unit=Units.DATA_SIZE.BIBYTE
        )
        disk.define_metric(
            "used_space", "Used Space", is_discrete=True, unit=Units.DATA_SIZE.BIBYTE
        )
        disk.define_metric(
            "free_space", "Free Space", is_discrete=True, unit=Units.DATA_SIZE.BIBYTE
        )
        disk.define_metric(
            "percent_used_space",
            "Disk Utilization",
            unit=Units.RATIO.PERCENT,
            is_key_attribute=True,
        )

        system = definition.define_object_type("system", "System")

        logger.debug(f"Returning adapter definition: {definition.to_json()}")
        return definition


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

            # Read the 'ID' identifier in the adapter instance and use it for a
            # connection test.
            id = adapter_instance.get_identifier_value("ID")

            # In this case the adapter does not need to connect
            # to anything, as it reads directly from the host it is running on.
            if id is None:
                result.with_error("No ID Found")
            elif id.lower() == "bad":
                # As there is not an actual failure condition to test for, this
                # example only shows the mechanics of reading identifiers and
                # constructing test results. Here we add an error to the result
                # that is returned.
                result.with_error("The ID is bad")
            # otherwise, the test has passed
        except Exception as e:
            logger.error("Unexpected connection test error")
            logger.exception(e)
            result.with_error("Unexpected connection test error: " + repr(e))
        finally:
            # TODO: If any connections are still open, make sure they are closed before returning
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

            # CPU
            cpu = result.object(ADAPTER_KIND, "cpu", "CPU")
            # properties
            cpu_count_property = Property("cpu_count", psutil.cpu_count())
            cpu.add_property(cpu_count_property)

            # metrics
            cpu_percent = Metric("cpu_percent", psutil.cpu_percent(1))
            user, nice, system, idle, *_ = psutil.cpu_times()

            user_time = Metric("user_time", user)
            nice_time = Metric("nice_time", nice)
            system_time = Metric("system_time", system)
            idle_time = Metric("idle_time", idle)

            # adding metrics to CPU
            cpu.add_metric(user_time)
            cpu.add_metric(nice_time)
            cpu.add_metric(system_time)
            cpu.add_metric(idle_time)

            # Disk
            disk = result.object(ADAPTER_KIND, "disk", "Disk")
            # gathering properties
            partition, mount_point, *_ = psutil.disk_partitions().pop()
            partition_property = Property("partition", partition)

            # adding properties
            disk.add_property(partition_property)

            # gathering metrics
            total, used, free, percent = psutil.disk_usage(mount_point)

            total_space = Metric("total_space", total)
            used_space = Metric("used_space", used)
            free_space = Metric("free_space", free)
            percent_used_space = Metric("percent_used_space", percent)

            # adding metrics to Disk
            disk.add_metric(total_space)
            disk.add_metric(used_space)
            disk.add_metric(free_space)
            disk.add_metric(percent_used_space)

            # Add system object to demonstrate relationships
            system = result.object(ADAPTER_KIND, "system", "System")

            system.add_child(disk)
            system.add_child(cpu)
        except Exception as e:
            logger.error("Unexpected collection error")
            logger.exception(e)
            result.with_error("Unexpected collection error: " + repr(e))
        finally:
            # TODO: If any connections are still open, make sure they are closed before returning
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
