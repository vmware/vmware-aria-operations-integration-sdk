import sys
import os
import json
import psutil


#TODO catch possible errors and add them to error response


class Collector:
    def __init__(self):
        #get connection parameters
        print("initializing collector")
        self.connect()

    def connect(self):
        #connect to service/other
        print("connecting...")

    def test(self):
        #ensure that there is communication  somehow
        print("Python test")


    def collect(self):

        # CPU
        cpu = Object("CPU", "Containerized Adapter","CPU")

        # properties
        cpu_count = Property("cpu_count",psutil.cpu_count())
        cpu.add_property(cpu_count)

        # metrics
        cpu_percent = Metric("cpu_percent",psutil.cpu_percent(1))
        user, nice, system, idle, *_ = psutil.cpu_times()

        user_time = Metric("user_time",user)
        nice_time = Metric("nice_time", nice)
        system_time = Metric("system_time",system)
        idle_time = Metric("idle_time",idle)

        # adding metrics to CPU
        cpu.add_metric(cpu_count)
        cpu.add_metric(user_time)
        cpu.add_metric(nice_time)
        cpu.add_metric(system_time)
        cpu.add_metric(idle_time)

        # Disk
        disk = Object("Disk", "Containerized Adapter", "Disk")
        # gathering properties
        partition, *_ = psutil.disk_partitions().pop()
        partition_property = Property("partition", partition)

        # adding properties
        disk.add_property(partition_property)

        # gathering metrics
        total, used, free, percent = psutil.disk_usage(partition)

        total_space = Metric("total_space", total)
        used_space = Metric("used_space", used)
        free_space = Metric("free_space", free)
        percent_used_space = Metric("percent_used_space", percent)

        # adding metrics to Disk
        disk.add_metric(total_space)
        disk.add_metric(used_space)
        disk.add_metric(free_space)
        disk.add_metric(percent_used_space)

        #TODO: create system object to show user relationships
        #TODO: create Result

class Metric:
    def __init__(self, key: str, value: int):
        self.key = key
        self.value = value
        self.timestamp = -1

    def to_string(self):
        return {
                "key": self.key,
                "numberValue": self.value,
                "timestamp": self.timestamp
                }



class Property:
    def __init__ (self, key: str, value ):
        #TODO: parse value and check whether is a string or a number
          self.key = key
          self.value = value,
          self.timestamp = -1

    def to_string(self):
        return {
                "key": self.key,
                "stringValue": self.value,
                "numberValue": self.value,
                "timestamp": self.timestamp
                }

class Object: #NOTE: maybe extend JSONEncoder or maybe do that in Result Object
    metrics = []
    properties = []
    def __init__(self, name: str, adapterKind: str, objectKind: str):
        self.name = name
        self.adapterKind = adapterKind
        self.objectKind = objectKind

    def add_metric(self, metric: Metric):
        #TODO: error handling maybe ?
        self.metrics.append(metric)

    def add_property(self, property_: Property):
        self.properties.append(property_)

#
#class Event:
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
#class Identifier:
#    def __init__(self, key: str, value: str, isPartOfUniqueness: bool):
#        #TODO constructor
#
#class Result:
#    def __init__(self, name: str, adapterKind: str, bojectKind: str, identifiers:[], ):
#
#        def object():
#            {
#                    "result": [
#                        {
#                            "key": {
#                                #Object
#                                },
#                            "metrics": [
#                                #Metric
#                                ],
#                            "properties": [
#                                #Property
#                                ],
#                            "events": [
#                                #Event
#                                ]
#                            }
#                        ],
#                    "metrics": [
#                               {
#                                 "key": "string",
#                                 "numberValue": 0,
#                                 "timestamp": -1
#                               }
#                             ],
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


def main(argv):
    collector = Collector()
    if len(argv) == 0:
        print("No arguments")
    elif argv[0] in 'collect':
        #collect()
        collector.collect()
    elif argv[0] in 'test':
        #test()
        collector.test()
    else:
        print(f"Command {argv[0]} not found")

if __name__ == '__main__':
    main(sys.argv[1:])
