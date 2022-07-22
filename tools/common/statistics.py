from collections import defaultdict
from dataclasses import dataclass
from statistics import median, stdev


@dataclass(frozen=True)
class ObjectKind:
    adapterKind: str
    objectKind: str

    def __repr__(self):
        return f"{self.adapterKind}::{self.objectKind}"


def _get_type(json) -> ObjectKind:
    if not json:
        return None
    if "adapterKind" not in json:
        object_key = json.get("key", {})
    else:
        object_key = json
    adapter_type = object_key.get("adapterKind")
    object_type = object_key.get("objectKind")
    if adapter_type and object_type:
        return ObjectKind(adapter_type, object_type)
    return None


class Stats:
    def __init__(self, array):
        self.count = sum(array)
        self.median = median(array)
        self.stddev = float("NaN")
        if len(array) > 2:
            self.stddev = stdev(array)

    def __repr__(self):
        return f"{self.count:0.2f}/{self.median:0.2f}/{self.stddev:0.2f}"


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
