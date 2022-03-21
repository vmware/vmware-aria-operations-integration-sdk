import json
import logging
import os
import sys
import time

import psutil

from constants import ADAPTER_KIND


def connect(self):
    # connect to service/other
    pass


def test():
    # Read the 'ID' identifier in the adapter instance and use it for a connection test
    if "ID" not in os.environ:
        return {"errorMessage": "No ID Found"}
    elif os.getenv("ID").lower() == "bad":
        return {"errorMessage": "The ID is bad"}
    else:
        # Empty dictionary means the test has passed
        return {}


def collect():
    # CPU
    cpu = Object("CPU", ADAPTER_KIND, "CPU")

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
    disk = Object("Disk", ADAPTER_KIND, "Disk")
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
    system = Object("System", ADAPTER_KIND, "System")

    system.add_child(disk)
    system.add_child(cpu)

    result = Result([cpu, disk, system])

    return result.get_json()


class Metric:
    def __init__(self, key: str, value: float):
        self.key = key
        self.value = value
        self.timestamp = int(time.time() * 1000)

    def get_json(self):
        return {
            "key": self.key,
            "numberValue": float(self.value),
            "timestamp": self.timestamp
        }


class Property:
    def __init__(self, key: str, value):
        self.key = key
        self.value = value
        self.timestamp = int(time.time() * 1000)

    def get_json(self):
        if isinstance(self.value, str):
            label = "stringValue"
        else:
            label = "numberValue"
            self.value = float(self.value)

        return {
            "key": self.key,
            label: self.value,
            "timestamp": self.timestamp
        }


class Object:  # NOTE: maybe extend JSONEncoder or maybe do that in Result Object
    metrics = []
    properties = []
    parents = []
    children = []

    def __init__(self, name: str, adapterkind: str, objectkind: str):
        self.name = name
        self.adapterkind = adapterkind
        self.objectkind = objectkind

    def add_metric(self, metric: Metric):
        # TODO: error handling
        self.metrics.append(metric)

    def add_property(self, property_: Property):
        self.properties.append(property_)

    def add_parent(self, parent):
        self.parents.append(parent)

    def add_child(self, child):
        self.children.append(child)

    def get_json(self):
        return {
            "key": {
                "name": f"{self.name}",
                "adapterKind": f"{self.adapterkind}",
                "objectKind": f"{self.objectkind}",
                # TODO: add identifiers
                "identifiers": []
            },
            "metrics": [metric.get_json() for metric in self.metrics],
            "properties": [prop.get_json() for prop in self.properties],
            # TODO: add events
            "events": []
        }


class Result:
    relationships = []

    def __init__(self, objects=None):
        if objects is None:
            objects = []
        self.objects = objects

    # TODO: create relationships by parsing objects
    def add_object(self, object_: Object):
        self.objects.append(object_)

    def get_json(self):
        return {
            "result": [obj.get_json() for obj in self.objects],
        }


#                    "result": [Object1, Object2, Object3 ... ObjectN],
#
#                    "relationships": [
#                        {
#                            "parent": {
#                                #Object
#                                },
#                            "children": [
#                                {
#                                    #Object
#                                    }
#                                ]
#                            }
#                        ],
#                    "notExistingObjects": [
#                        {
#                            #Object
#                            }
#                        ],
#                    "errorMessage": "string"
#                    }

# class Event:
#    def __init__(self, criticality: str, message: str, faultKey, autocancel = False,  startDate, updateDate, cancelDate, watchWaitCyccle, cancelWaitCycle):
#        self.criticality = criticality
#        self.message = message
#        self.faultkey = faultkey
#        self.autocancel = autocancel
#        self.startDate = startDate
#        self.updateDate = updateDate
#        sefl.cancelDate = cancelDate
#        self.watchWaitCycle = watchWaitCycle
#        self.cancelWaitCycle = cancelWaitCycle
#
#
#    def to_string(self):
#        return {
#                "criticality": self.criticality,
#                "message": self.message,
#                "faultKey": self.faultkey,
#                "autoCancel": self.autocancel,
#                "startDate": self.startDate,
#                "updateDate": self.updateDate,
#                "cancelDate": sefl.cancelDate,
#                "watchWaitCycle": self.watchWaitCycle,
#                "cancelWaitCycle": self.cancelWaitCycle
#                }
#
# class Identifier:
#    def __init__(self, key: str, value: str, isPartOfUniqueness: bool):
#        #TODO constructor
#


def main(argv):
    try:
        logging.basicConfig(filename="/var/log/adapter.log",
                            filemode="a",
                            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
                            datefmt="%H:%M:%S",
                            level=logging.DEBUG)
    except Exception as e:
        logging.basicConfig(level=logging.CRITICAL+1)

    logger = logging.getLogger("adapter")
    if len(argv) != 2:
        logger.debug("Arguments must be <method> <ouputfile>")
    elif argv[0] == "collect":
        to_server(argv[1], collect())
    elif argv[0] == "test":
        to_server(argv[1], test())
    elif argv[0] == "endpoint_urls":
        to_server(argv[1], [])
    else:
        logger.debug(f"Command {argv[0]} not found")


def to_server(fifo, result):
    logger = logging.getLogger("adapter")
    logger.debug(repr(result))
    logger.debug(f"FIFO = {fifo}")
    try:
        with open(fifo, "w") as output_file:
            logger.debug(f"Opened {fifo}")
            json.dump(result, output_file)
            logger.debug(f"Closing {fifo}")
    except Exception as e:
        logger.debug(e)
    logger.debug("Finished writing results to FIFO")


if __name__ == "__main__":
    main(sys.argv[1:])
