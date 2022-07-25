from collections import defaultdict
from dataclasses import dataclass
from statistics import median, stdev

from common.describe import is_true


@dataclass(frozen=True)
class ObjectType:
    adapterKind: str
    objectKind: str

    def __repr__(self):
        return f"{self.adapterKind}::{self.objectKind}"


def _get_type(json) -> ObjectType:
    if not json:
        return None
    if "adapterKind" not in json:
        object_key = json.get("key", {})
    else:
        object_key = json
    adapter_type = object_key.get("adapterKind")
    object_type = object_key.get("objectKind")
    if adapter_type and object_type:
        return ObjectType(adapter_type, object_type)
    return None


@dataclass(frozen=True)
class Identifier:
    key: str
    value: str

    def __repr__(self):
        return f"{self.key}: {self.value}"


def _get_identifier(json) -> Identifier:
    if not json:
        return None
    if json.get("isPartOfUniqueness"):
        key = json.get("key")
        value = json.get("value")
        return Identifier(key, value)
    return None


def _get_identifiers(json) -> [Identifier]:
    if not json:
        return []
    identifiers = json.get("identifiers", [])
    identifiers = [_get_identifier(identifier) for identifier in identifiers]
    return [identifier for identifier in identifiers if identifier is not None].sort(
        key=lambda identifier: identifier.key)


@dataclass(frozen=True)
class ObjectId:
    name: str
    objectKind: ObjectType
    identifiers: [Identifier]

    def __repr__(self):
        return f"{self.name} ({self.objectKind})"


def _get_object(json) -> ObjectId:
    if not json:
        return None
    name = json.get("name")
    object_type = _get_type(json)
    identifiers = _get_identifiers(json)
    return ObjectId(name, object_type, identifiers)


class Stats:
    def __init__(self, array):
        self.datapoints = len(array)
        self.count = sum(array)
        self.median = median(array)
        self.min = min(array)
        self.max = max(array)
        self.stddev = float("NaN")
        if len(array) > 2:
            self.stddev = stdev(array)

    def __repr__(self):
        if self.datapoints <= 1 or self.count == 0:
            return f"{self.count}"
        else:
            return f"{self.count} ({self.min}/{self.median}/{self.max})"


class ObjectStatistics:
    def __init__(self, json):
        self.key = json.get("key")  # TODO: Make this a comparable class rather than just raw json
        self.events = [event.get("message") for event in json.get("events", [])]
        self.metrics = [metric.get("key") for metric in json.get("metrics", [])]
        self.properties = [property.get("key") for property in json.get("properties", [])]

    def get_event_count(self):
        return len(self.events)

    def get_metric_count(self):
        return len(self.metrics)

    def get_property_count(self):
        return len(self.properties)


class ObjectTypeStatistics:
    def __init__(self):
        self.object_type = None
        self.objects = []

    def add_object(self, object_json):
        if self.object_type is None:
            self.object_type = _get_type(object_json)
        elif self.object_type != _get_type(object_json):
            return
        self.objects.append(ObjectStatistics(object_json))

    def get_object_count(self):
        return len(self.objects)

    def get_event_count(self):
        return sum(obj.get_event_count() for obj in self.objects)

    def get_metric_count(self):
        return sum(obj.get_metric_count() for obj in self.objects)

    def get_property_count(self):
        return sum(obj.get_property_count() for obj in self.objects)

    def get_event_counts(self):
        return [obj.get_event_count() for obj in self.objects]

    def get_metric_counts(self):
        return [obj.get_metric_count() for obj in self.objects]

    def get_property_counts(self):
        return [obj.get_property_count() for obj in self.objects]

    def get_summary(self):
        return {
            "objects": self.get_object_count(),
            "events": Stats(self.get_event_counts()),
            "metrics": Stats(self.get_metric_counts()),
            "properties": Stats(self.get_property_counts())
        }


class LongCollectionStatistics:
    def __init__(self):
        self.object_collection_history = {}
        self.num_collections = 0
        self.collections_intervals = []

    def add(self, json, elapsed_time):
        # TODO: get CPU and memory usage
        self.num_collections += 1
        self.collections_intervals.append(elapsed_time)
        collection_stats = CollectionStatistics(json, elapsed_time)
        for obj_statistics in collection_stats.obj_statistics.values():
            if obj_statistics.object_type not in self.object_collection_history:
                self.object_collection_history[obj_statistics.object_type] = {
                    "object_count": [obj_statistics.get_object_count()],
                    "metric_count": [obj_statistics.get_metric_count()],
                    "property_count": [obj_statistics.get_property_count()],
                    "event_count": [obj_statistics.get_event_count()],
                }
            else:
                self.object_collection_history[obj_statistics.object_type]["object_count"].append(
                    obj_statistics.get_object_count())
                self.object_collection_history[obj_statistics.object_type]["metric_count"].append(
                    obj_statistics.get_metric_count())
                self.object_collection_history[obj_statistics.object_type]["property_count"].append(
                    obj_statistics.get_property_count())
                self.object_collection_history[obj_statistics.object_type]["event_count"].append(
                    obj_statistics.get_event_count())


class CollectionStatistics:
    def __init__(self, json, duration):
        self.duration = duration
        self.obj_statistics = defaultdict(lambda: ObjectTypeStatistics())
        self.rel_statistics = defaultdict(lambda: 0)
        self.get_counts(json)

    def get_counts(self, json):
        for obj in json.get("result", []):
            object_type = _get_type(obj)
            if object_type:
                stats = self.obj_statistics[object_type]
                stats.add_object(obj)
        for rel in json.get("relationships", []):
            parent = rel.get("parent", None)
            parent_type = _get_type(parent)
            if parent_type:
                children = rel.get("children", [])
                for child in children:
                    child_type = _get_type(child)
                    if child_type:
                        key = (parent_type, child_type)
                        self.rel_statistics[key] += 1

    def __repr__(self):
        headers = ["Object Type", "Count", "Metrics", "Properties", "Events"]
        data = []

        for stats in list(self.obj_statistics.values()):
            summary = stats.get_summary()
            data.append(
                [stats.object_type, summary["objects"], summary["metrics"], summary["properties"], summary["events"]])
        obj_table = str(Table(headers, data))

        headers = ["Parent Type", "Child Type", "Count"]
        data = []
        for (parent_object_type, child_object_type), count in list(self.rel_statistics.items()):
            data.append([parent_object_type, child_object_type, count])
        rel_table = str(Table(headers, data))

        duration = f"Collection completed in {self.duration:0.2f} seconds.\n"
        return "Collection summary: \n\n" + obj_table + "\n" + rel_table + "\n" + duration


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
