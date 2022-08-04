#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

from collections import defaultdict
from statistics import median, stdev

from common.docker_wrapper import calculate_cpu_percent_latest_unix
from sen.util import calculate_blkio_bytes, calculate_network_bytes
from common.model import _get_object_id, ObjectId


class Stats:
    def __init__(self, array):
        self.data_points = len(array)
        self.count = sum(array)
        self.median = median(array)
        self.min = min(array)
        self.max = max(array)
        self.stddev = float("NaN")
        if len(array) > 2:
            self.stddev = stdev(array)

    def __repr__(self):
        if self.data_points <= 1 or self.count == 0:
            return f"{self.count}"
        else:
            return f"{self.count} ({self.min}/{self.median}/{self.max})"


class ObjectStatistics:
    def __init__(self, json):
        self.key = _get_object_id(json.get("key"))
        self.events = set(event.get("message") for event in json.get("events", []))
        self.metrics = set(metric.get("key") for metric in json.get("metrics", []))
        self.properties = set(property.get("key") for property in json.get("properties", []))
        self.string_properties = {property.get("key"): property.get("stringValue") for property in
                                  json.get("properties", []) if "stringValue" in property}
        self.parents = set()
        self.children = set()

    def add_parent(self, parent: ObjectId):
        self.parents.add(parent)

    def add_child(self, child: ObjectId):
        self.children.add(child)

    def get_event_count(self):
        return len(self.events)

    def get_metric_count(self):
        return len(self.metrics)

    def get_property_count(self):
        return len(self.properties)

    def get_parent_count(self):
        return len(self.parents)

    def get_children_count(self):
        return len(self.children)


class ObjectTypeStatistics:
    def __init__(self):
        self.object_type = None
        self.objects = []

    def add_object(self, obj: ObjectStatistics):
        if self.object_type is None:
            self.object_type = obj.key.objectKind
        elif self.object_type != obj.key.objectKind:
            return
        self.objects.append(obj)

    def get_object_count(self):
        return len(self.objects)

    def get_event_count(self):
        return sum(obj.get_event_count() for obj in self.objects)

    def get_metric_count(self):
        return sum(obj.get_metric_count() for obj in self.objects)

    def get_property_count(self):
        return sum(obj.get_property_count() for obj in self.objects)

    def get_children_count(self):
        return sum(obj.get_children_count() for obj in self.objects)

    def get_parent_count(self):
        return sum(obj.get_parent_count() for obj in self.objects)

    def get_objects(self):
        return self.objects

    def get_event_counts(self):
        return [obj.get_event_count() for obj in self.objects]

    def get_metric_counts(self):
        return [obj.get_metric_count() for obj in self.objects]

    def get_property_counts(self):
        return [obj.get_property_count() for obj in self.objects]

    def get_children_counts(self):
        return [obj.get_children_count() for obj in self.objects]

    def get_parent_counts(self):
        return [obj.get_parent_count() for obj in self.objects]

    def get_summary(self):
        return {
            "objects": self.get_object_count(),
            "events": Stats(self.get_event_counts()),
            "metrics": Stats(self.get_metric_counts()),
            "properties": Stats(self.get_property_counts()),
            "parents": Stats(self.get_parent_counts()),
            "children": Stats(self.get_children_counts())
        }


class LongCollectionStatistics:
    def __init__(self):
        self.collection_statistics = []

    def add(self, collection_statistic):
        self.collection_statistics.append(collection_statistic)

    def get_collection_statistics(self):
        object_collection_history = {}
        collection_interval = []
        for collection_stat in self.collection_statistics:
            collection_interval.append(collection_stat.duration)
            for obj_statistics in collection_stat.obj_type_statistics.values():
                if obj_statistics.object_type not in object_collection_history:
                    object_collection_history[obj_statistics.object_type] = {
                        "object_count": [obj_statistics.get_object_count()],
                        "metric_count": [obj_statistics.get_metric_count()],
                        "property_count": [obj_statistics.get_property_count()],
                        "event_count": [obj_statistics.get_event_count()],
                    }
                else:
                    object_collection_history[obj_statistics.object_type]["object_count"].append(
                        obj_statistics.get_object_count())
                    object_collection_history[obj_statistics.object_type]["metric_count"].append(
                        obj_statistics.get_metric_count())
                    object_collection_history[obj_statistics.object_type]["property_count"].append(
                        obj_statistics.get_property_count())
                    object_collection_history[obj_statistics.object_type]["event_count"].append(
                        obj_statistics.get_event_count())
        return {"num_collections": len(self.collection_statistics),
                "intervals": collection_interval,
                "stats": object_collection_history}


class ContainerStats:
    def __init__(self, initial_stats, current_stats):
        self.get_stats(initial_stats, current_stats)

    def get_stats(self, initial_stats, current_stats):
        self.block_read, self.block_write  = calculate_blkio_bytes(current_stats)
        self.network_read, self.network_write = calculate_network_bytes(current_stats)
        self.current_memory_usage = current_stats["memory_stats"]["usage"]
        # TODO: calculate cpu percent for Windows
        self.cpu_percent_usage = calculate_cpu_percent_latest_unix(initial_stats, current_stats)
        self.total_memory = current_stats["memory_stats"]["limit"]
        self.memory_percent_usage = (self.current_memory_usage / current_stats["memory_stats"]["limit"]) * 100.0


def convert_bytes(bytes_number):
    tags = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]

    i = 0
    double_bytes = bytes_number

    while i < len(tags) and bytes_number >= 1024:
        double_bytes = bytes_number / 1024.0
        i = i + 1
        bytes_number = bytes_number / 1024

    return str(round(double_bytes, 2)) + " " + tags[i]


class CollectionStatistics:
    def __init__(self, json, container_stats, duration):
        self.duration = duration
        self.obj_type_statistics = defaultdict(lambda: ObjectTypeStatistics())
        self.obj_statistics = {}
        self.rel_statistics = defaultdict(lambda: 0)
        self.container_stats = container_stats
        self.get_counts(json)

    def get_counts(self, json):
        for obj in json.get("result", []):
            obj_id = _get_object_id(obj.get("key"))
            if obj_id:
                stats = ObjectStatistics(obj)
                self.obj_statistics[obj_id] = stats
                self.obj_type_statistics[obj_id.objectKind].add_object(stats)
        for rel in json.get("relationships", []):
            parent = _get_object_id(rel.get("parent"))
            children = rel.get("children", [])
            for child in children:
                child = _get_object_id(child)
                if child and parent:
                    key = (parent.objectKind, child.objectKind)
                    self.rel_statistics[key] += 1
                    self.obj_statistics[parent].add_child(child)
                    self.obj_statistics[child].add_parent(parent)

    def __repr__(self):
        headers = ["Object Type", "Count", "Metrics", "Properties", "Events", "Parents", "Children"]
        data = []

        for stats in list(self.obj_type_statistics.values()):
            summary = stats.get_summary()
            data.append(
                [stats.object_type, summary["objects"], summary["metrics"], summary["properties"], summary["events"],
                 summary["parents"], summary["children"]])
        obj_table = str(Table(headers, data))

        headers = ["Parent Type", "Child Type", "Count"]
        data = []
        for (parent_object_type, child_object_type), count in list(self.rel_statistics.items()):
            data.append([parent_object_type, child_object_type, count])
        rel_table = str(Table(headers, data))

        headers = ["Avg CPU %", "Avg Memory Usage %", "Memory Limit", "Network I/O", "Block I/O"]
        data = [[f"{self.container_stats.cpu_percent_usage:.2f} %",
                 f"{self.container_stats.memory_percent_usage:.2f} %",
                 convert_bytes(self.container_stats.total_memory),
                 f"{convert_bytes(self.container_stats.network_read)} / {convert_bytes(self.container_stats.network_write)}",
                 f"{convert_bytes(self.container_stats.block_read)} / {convert_bytes(self.container_stats.block_write)}"]]
        table = Table(headers, data)
        container_table = str(table)

        duration = f"Collection completed in {self.duration:0.2f} seconds.\n"
        return "Collection summary: \n\n" + obj_table + "\n" + rel_table + "\n" + container_table + "\n" + duration


class Table:
    def __init__(self, headers: [], data: [[]]):
        # Convert each header/cell to a string - otherwise won't work with len() and format() functions
        self.headers = [str(header) for header in headers]
        self.data = [[str(col) for col in row] for row in data]

    def __repr__(self):
        output = ""
        column_sizes = []
        horizontal_rule = []
        for col in range(len(self.headers)):
            size = len(self.headers[col])
            for row in self.data:
                size = max(size, len(row[col]))
            column_sizes.append("{:<" + str(size) + "}")
            horizontal_rule.append("-" * size)
        formatting = " | ".join(column_sizes)

        output += formatting.format(*self.headers) + "\n"
        output += "-+-".join(horizontal_rule) + "\n"
        for row in self.data:
            output += formatting.format(*row) + "\n"

        return output
