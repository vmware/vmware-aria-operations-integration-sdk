import logging
import os
import sys

import psutil

from constants import ADAPTER_KIND
from vrops.adapter_instance import AdapterInstance
from vrops.attribute import Property, Metric
from vrops.pipe_utils import write_to_pipe
from vrops.result import Result

logger = logging.getLogger("adapter")


def test(adapter_instance: AdapterInstance):
    # Read the 'ID' identifier in the adapter instance and use it for a connection test
    if "ID" not in os.environ:
        return {"errorMessage": "No ID Found"}
    elif os.getenv("ID").lower() == "bad":
        return {"errorMessage": "The ID is bad"}
    else:
        # Empty dictionary means the test has passed
        return {}


def collect(adapter_instance: AdapterInstance):
    result = Result()
    try:
        logger.debug("Starting collection")
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

        # TODO: create system object to show user relationships
        system = result.object(ADAPTER_KIND, "System", "System")

        system.add_child(disk)
        system.add_child(cpu)

        logger.debug(f"Returning collection result {result}")
        return result
    except Exception as e:
        logger.exception(e)
        result.with_error(repr(e))
        return result


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
        logger.debug("Arguments must be <method> <inputfile> <ouputfile>")
        exit(1)

    command, infile, outfile = argv

    adapter_instance = AdapterInstance.from_input(infile)

    if command == "collect":
        collect(adapter_instance).send_results(outfile)
    elif command == "test":
        write_to_pipe(outfile, test(adapter_instance))
    elif command == "endpoint_urls":
        write_to_pipe(outfile, [])
    else:
        logger.debug(f"Command {command} not found")
        exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
