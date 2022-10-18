#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import logging
import sys

import psutil

from constants import ADAPTER_KIND
from aria.ops.adapter_instance import AdapterInstance
from aria.ops.attribute import Property, Metric
from aria.ops.result import EndpointResult, CollectResult, TestResult

logger = logging.getLogger(__name__)


def test(adapter_instance: AdapterInstance) -> TestResult:
    result = TestResult()
    try:
        # Sample test connection code follows. Replace with your own test connection code.
        # A typical test connection will generally consist of:
        # 1. Read identifier values from adapter_instance that are required to
        #    connect to the target(s)
        # 2. Connect to the target(s), and retrieve some sample data
        # 3. Disconnect cleanly from the target (ensure this happens even if an error occurs)
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
        return result

    except Exception as e:
        # TODO: If any connections are still open, make sure they are closed before returning
        logger.error("Unexpected connection test error")
        logger.exception(e)
        result.with_error("Unexpected connection test error: " + repr(e))
        return result


def get_endpoints(adapter_instance: AdapterInstance) -> EndpointResult:
    result = EndpointResult()
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
    # and VMware Aria Operations will use the results to extract a certificate from
    # each URL. If the certificate is not trusted by the VMware Aria Operations Trust
    # Store, the user will be prompted to either accept or reject the certificate. If
    # it is accepted, the certificate will be added to the AdapterInstance object that
    # is passed to the 'test' and 'collect' methods. Any certificate that is
    # encountered in those methods should then be validated against the certificate(s)
    # in the AdapterInstance.
    return result


def collect(adapter_instance: AdapterInstance) -> CollectResult:
    result = CollectResult()
    try:
        logger.debug("Starting collection")
        # Sample collection code follows. Replace this with your own collection code.
        # A typical collection will generally consist of:
        # 1. Read identifier values from adapter_instance that are required to
        #    connect to the target(s)
        # 2. Connect to the target(s), and retrieve data
        # 3. Add the data into a CollectResult's objects, properties, metrics, etc
        # 4. Disconnect cleanly from the target (ensure this happens even if an error occurs)
        # 5. Return the CollectResult.

        # CPU
        cpu = result.object(ADAPTER_KIND, "CPU", "CPU")
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
        disk = result.object(ADAPTER_KIND, "Disk", "Disk")
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
        system = result.object(ADAPTER_KIND, "System", "System")

        system.add_child(disk)
        system.add_child(cpu)

        logger.debug(f"Returning collection result {result}")
        return result
    except Exception as e:
        # TODO: If any connections are still open, make sure they are closed before returning
        logger.error("Unexpected collection error")
        logger.exception(e)
        result.with_error("Unexpected collection error: " + repr(e))
        return result


# Main entry point of the adapter. You should not need to modify anything below this line.
def main(argv):
    try:
        logging.basicConfig(filename="/var/log/adapter.log",
                            filemode="a",
                            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
                            datefmt="%H:%M:%S",
                            level=logging.DEBUG)
    except Exception as e:
        logging.basicConfig(level=logging.CRITICAL + 1)

    logger.debug(f"Running adapter code with arguments: {argv}")
    if len(argv) != 3:
        # `inputfile` and `outputfile` are always automatically appended to the
        # argument list by the server
        logger.debug("Arguments must be <method> <inputfile> <ouputfile>")
        exit(1)

    method = argv[0]
    adapter_instance = AdapterInstance.from_input()

    if method == "test":
        test(adapter_instance).send_results()
    elif method == "endpoint_urls":
        get_endpoints(adapter_instance).send_results()
    elif method == "collect":
        collect(adapter_instance).send_results()
    else:
        logger.debug(f"Command {method} not found")
        exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
