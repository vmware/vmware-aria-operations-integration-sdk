#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

from collections import defaultdict
from statistics import median, stdev

from vrealize_operations_integration_sdk.model import _get_object_id, ObjectId


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


class UniqueObjectTypeStatistics:
    def __init__(self):
        self.running_collection = set()
        self.data_points = list()
        self.counts = list()

    def add(self, unique_items, total_items):
        self.running_collection.update(unique_items)
        self.data_points.append(len(self.running_collection))
        self.counts.append(total_items)


class LongObjectTypeStatistics:
    def __init__(self):
        self.objects_stats = UniqueObjectTypeStatistics()
        self.metrics_stats = UniqueObjectTypeStatistics()
        self.properties_stats = UniqueObjectTypeStatistics()
        self.events_stats = UniqueObjectTypeStatistics()
        self.relationships_stats = UniqueObjectTypeStatistics()
        self.string_property_values_stats = UniqueObjectTypeStatistics()

    def add(self, _object):
        self.objects_stats.add(_object.get_unique_objects(), _object.get_object_count())
        self.metrics_stats.add(_object.get_unique_metrics(), _object.get_metric_count())
        self.properties_stats.add(_object.get_unique_properties(), _object.get_property_count())
        self.events_stats.add(_object.get_unique_events(), _object.get_event_count())
        unique_relationships = _object.get_unique_relationships()
        self.relationships_stats.add(unique_relationships, len(unique_relationships))
        self.string_property_values_stats.add(_object.get_unique_string_property_values(), 0)

    def get_growth_rates(self):
        return [f"{get_growth_rate(self.objects_stats.data_points):.2f} %",
                f"{get_growth_rate(self.metrics_stats.data_points):.2f} %",
                f"{get_growth_rate(self.properties_stats.data_points):.2f} %",
                f"{get_growth_rate(self.string_property_values_stats.data_points):.2f} %",
                f"{get_growth_rate(self.events_stats.data_points):.2f} %",
                f"{get_growth_rate(self.relationships_stats.data_points):.2f} %"]

    def get_summary(self):
        return {
            "objects": Stats(self.objects_stats.counts),
            "events": Stats(self.events_stats.counts),
            "metrics": Stats(self.metrics_stats.counts),
            "properties": Stats(self.properties_stats.counts),
            "relationships": Stats(self.relationships_stats.counts),
        }


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

    def get_unique_objects(self):
        unique_objects = set()
        for _object in self.objects:
            unique_objects.add(_object.key)

        return unique_objects

    def get_unique_metrics(self):
        unique_metrics = set()
        for _object in self.objects:
            unique_metrics.update(_object.metrics)

        return unique_metrics

    def get_unique_properties(self):
        unique_properties = set()
        for _object in self.objects:
            unique_properties.update(_object.properties)

        return unique_properties

    def get_unique_string_property_values(self):
        unique_string_property_values = set()
        for _object in self.objects:
            unique_string_property_values.update(_object.string_properties.values())

        return unique_string_property_values

    def get_unique_events(self):
        unique_events = set()
        for _object in self.objects:
            unique_events.update(_object.events)

        return unique_events

    def get_unique_relationships(self):
        unique_relationships = set()
        for _object in self.objects:
            unique_relationships.update([(parent, _object.key) for parent in _object.parents])
            unique_relationships.update([(_object.key, child) for child in _object.children])

        return unique_relationships

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


def get_average(inputs: list):
    return sum(inputs) / len(inputs)


def get_growth_rate(inputs: list):
    present = inputs[-1]
    past = inputs[0]

    # Adding one to the formula allows us to account for cases where zero is the initial or final value
    if not (present and past):
        present += 1
        past += 1

    return (((present / past) ** (1 / len(inputs))) - 1) * 100


class LongCollectionStatistics:
    def __init__(self):
        self.collection_statistics = list()
        self.long_object_type_statistics = defaultdict(lambda: LongObjectTypeStatistics())

    def add(self, collection_statistic):
        self.collection_statistics.append(collection_statistic)
        for object_type, object_type_stat in collection_statistic.obj_type_statistics.items():
            self.long_object_type_statistics[object_type].add(object_type_stat)

    def __repr__(self):
        headers = ["Object Type", "Object Growth", "Metric Growth", "Property Growth", "Property Values Growth",
                   "Event Growth", "Relationship Growth"]
        data = []
        for resource_type, obj_type_statistics in self.long_object_type_statistics.items():
            data.append(
                [resource_type, *obj_type_statistics.get_growth_rates()])
        growth_table = str(Table(headers, data))

        headers = ["Object Type", "Count", "Metrics", "Properties", "Events", "Relationships"]
        data = []
        for resource_type, obj_type_statistics in self.long_object_type_statistics.items():
            summary = obj_type_statistics.get_summary()
            data.append(
                [resource_type, summary["objects"], summary["metrics"], summary["properties"], summary["events"],
                 summary["relationships"]])
        obj_table = str(Table(headers, data))

        headers = ["Collection", "Duration", "Avg CPU %", "Avg Memory Usage %", "Memory Limit", "Network I/O",
                   "Block I/O"]
        data = []
        for number, collection_stat in enumerate(self.collection_statistics):
            data.append([number + 1, f"{collection_stat.duration:.2f} s", *collection_stat.container_stats.get_stats()])
        collection_table = str(Table(headers, data))

        return "Long Collection summary:\n\n" + obj_table + "\n" + growth_table + "\n" + collection_table


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
        data = [self.container_stats.get_stats()]
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
