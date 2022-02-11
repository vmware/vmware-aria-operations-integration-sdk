import os

def build_template(path: str, root_directory: str):

    with open(os.path.join(path, root_directory, "collector.py"),'w') as collector:
        collector.write(
"""
import sys
import os
import json
import psutil

#NOTE: this is a demo version of the adapter

class Collector:
    def __init__(self):
        #get connection parameters

        def connect(self):
            #connect to service/other

    def test(self):
        #ensure that there is communication  somehow
        print("Python test")

    def collect(self):

        # CPU
        cpu = Object("CPU", "Containerized Adapter","CPU")

        # properties
        cpu_count_property  = Property("cpu_count",psutil.cpu_count())
        cpu.add_property(cpu_count_property)

        # metrics
        cpu_percent = Metric("cpu_percent",psutil.cpu_percent(1))
        user, nice, system, idle, *_ = psutil.cpu_times()

        user_time = Metric("user_time",user)
        nice_time = Metric("nice_time", nice)
        system_time = Metric("system_time",system)
        idle_time = Metric("idle_time",idle)

        # adding metrics to CPU
        cpu.add_metric(user_time)
        cpu.add_metric(nice_time)
        cpu.add_metric(system_time)
        cpu.add_metric(idle_time)

        # Disk
        disk = Object("Disk", "Containerized Adapter", "Disk")
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

        system = Object("System", "Containerized Adapter", "System")

        system.add_child(disk)
        system.add_child(cpu)

        result = Result([cpu,disk,system])

        print(result)

class Metric:
    def __init__(self, key: str, value: int):
        self.key = key
        self.value = value
        self.timestamp = -1

    def __str__(self):
                return f\"\"\"
        {{
            key: {self.key},
            numberValue: {self.value},
            timestamp: {self.timestamp}
        }}\"\"\"


class Property:
    def __init__ (self, key: str, value):
          self.key = key
          self.value = value
          self.timestamp = -1

    def __str__(self):
        label = 'numberValue' if type(self.value) == int or type(self.value) == float else 'stringValue'

        return f\"\"\"
        {{
          key: {self.key},
          {label}: {self.value},
          timestamp: {self.timestamp}
        }}\"\"\"

class Object:
    metrics = []
    properties = []
    parents = []
    children = []

    def __init__(self, name: str, adapterkind: str, objectkind: str):
        self.name = name
        self.adapterkind = adapterkind
        self.objectkind = objectkind

    def add_metric(self, metric: Metric):
        self.metrics.append(metric)

    def add_property(self, property_: Property):
        self.properties.append(property_)

    def add_parent(self, parent):
        self.parents.append(parent)

    def add_child(self, child):
        self.children.append(child)

    def __str__(self):
        return f\"\"\"
    {{
      name: {self.name},
      adapterKind: {self.adapterkind},
      objectKind: {self.objectkind},
      properties: [{','.join(map(str,self.properties))}],
      metrics: [{','.join(map(str,self.metrics))}]
    }}\"\"\"

class Result:
    relationships = []

    def __init__(self, objects = []):
        self.objects = objects

    #TODO: create relationships by parsing objects
    def add_object(self, object_: Object):
        objects.append(object)

    def __str__(self):
        return f\"\"\"
{{
  "result": [{','.join(map(str,self.objects))}],

}}\"\"\"

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
"""
        )
