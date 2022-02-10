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
        #TODO: should return Result Object
        #container statistics
        print("collecting")
        print()

        #object cpu
        print("CPU")
        #property
        print("----Properties----")
        cpu_count = psutil.cpu_count()
        print(f"cpu count: {cpu_count}")
        #metrics
        print("----Metrics----")
        cpu_percent = psutil.cpu_percent(1)
        print(f"cpu percent: {cpu_percent}")
        #metric: cpu times
        user, nice, system, idle, *_ = psutil.cpu_times()
        print(f"user time: {user}")
        print(f"nice time: {nice}")
        print(f"system time: {system}")
        print(f"idle time: {idle}")
        print()

        #object disk
        print("Disk")
        print("----Properties----")
        #property
        partition, *_ = psutil.disk_partitions().pop()
        print(f"name: {partition}")
        #metrics
        print("----Metrics----")
        #metric
        total, used, free, percent = psutil.disk_usage(partition)
        print(f"total space: {total}")
        print(f"used space: {used}")
        print(f"free space: {free}")
        print(f"percent used: {percent}")
        print()

        #object system
        #property
        #metric
        #metric




class Metric:
    def __init__(self, key: str, value, int):
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
