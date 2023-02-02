#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import defaultdict
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import TYPE_CHECKING

from vmware_aria_operations_integration_sdk.docker_wrapper import ContainerStats
from vmware_aria_operations_integration_sdk.model import _get_object_id
from vmware_aria_operations_integration_sdk.model import ObjectId
from vmware_aria_operations_integration_sdk.model import ObjectType

if TYPE_CHECKING:
    from vmware_aria_operations_integration_sdk.serialization import CollectionBundle
from vmware_aria_operations_integration_sdk.stats import get_growth_rate
from vmware_aria_operations_integration_sdk.stats import LongRunStats
from vmware_aria_operations_integration_sdk.stats import Stats
from vmware_aria_operations_integration_sdk.stats import UniqueObjectTypeStatistics
from vmware_aria_operations_integration_sdk.ui import Table
from vmware_aria_operations_integration_sdk.util import LazyAttribute


class ObjectStatistics:
    def __init__(self, json: Dict) -> None:
        key = _get_object_id(json.get("key"))
        if not key:
            raise Exception("Could not find key in json when creating ObjectStatistics")
        self.key = key
        self.events = set(event.get("message") for event in json.get("events", []))
        self.metrics = set(metric.get("key") for metric in json.get("metrics", []))
        self.properties = set(
            property.get("key") for property in json.get("properties", [])
        )
        self.string_properties = {
            prop.get("key"): prop.get("stringValue")
            for prop in json.get("properties", [])
            if "stringValue" in prop
        }
        self.parents: Set[ObjectId] = set()
        self.children: Set[ObjectId] = set()

    def add_parent(self, parent: ObjectId) -> None:
        self.parents.add(parent)

    def add_child(self, child: ObjectId) -> None:
        self.children.add(child)

    def get_event_count(self) -> int:
        return len(self.events)

    def get_metric_count(self) -> int:
        return len(self.metrics)

    def get_property_count(self) -> int:
        return len(self.properties)

    def get_parent_count(self) -> int:
        return len(self.parents)

    def get_children_count(self) -> int:
        return len(self.children)


class ObjectTypeStatistics:
    def __init__(self) -> None:
        self.object_type: Optional[ObjectType] = None
        self.objects: List[ObjectStatistics] = []

    def add_object(self, obj: ObjectStatistics) -> None:
        if self.object_type is None:
            self.object_type = obj.key.objectKind
        elif self.object_type != obj.key.objectKind:
            return
        self.objects.append(obj)

    def get_unique_objects(self) -> Set[ObjectId]:
        unique_objects = set()
        for _object in self.objects:
            unique_objects.add(_object.key)

        return unique_objects

    def get_unique_metrics(self) -> Set[str]:
        unique_metrics = set()
        for _object in self.objects:
            unique_metrics.update(_object.metrics)

        return unique_metrics

    def get_unique_properties(self) -> Set[str]:
        unique_properties = set()
        for _object in self.objects:
            unique_properties.update(_object.properties)

        return unique_properties

    def get_unique_string_property_values(self) -> Set[str]:
        unique_string_property_values: Set[str] = set()
        for _object in self.objects:
            unique_string_property_values.update(_object.string_properties.values())

        return unique_string_property_values

    def get_unique_events(self) -> Set[str]:
        unique_events = set()
        for _object in self.objects:
            unique_events.update(_object.events)

        return unique_events

    def get_unique_relationships(self) -> Set[Tuple[ObjectId, ObjectId]]:
        unique_relationships = set()
        for _object in self.objects:
            unique_relationships.update(
                [(parent, _object.key) for parent in _object.parents]
            )
            unique_relationships.update(
                [(_object.key, child) for child in _object.children]
            )

        return unique_relationships

    def get_object_count(self) -> int:
        return len(self.objects)

    def get_event_count(self) -> int:
        return sum(obj.get_event_count() for obj in self.objects)

    def get_metric_count(self) -> int:
        return sum(obj.get_metric_count() for obj in self.objects)

    def get_property_count(self) -> int:
        return sum(obj.get_property_count() for obj in self.objects)

    def get_children_count(self) -> int:
        return sum(obj.get_children_count() for obj in self.objects)

    def get_parent_count(self) -> int:
        return sum(obj.get_parent_count() for obj in self.objects)

    def get_objects(self) -> List[ObjectStatistics]:
        return self.objects

    def get_event_counts(self) -> List[int]:
        return [obj.get_event_count() for obj in self.objects]

    def get_metric_counts(self) -> List[int]:
        return [obj.get_metric_count() for obj in self.objects]

    def get_property_counts(self) -> List[int]:
        return [obj.get_property_count() for obj in self.objects]

    def get_children_counts(self) -> List[int]:
        return [obj.get_children_count() for obj in self.objects]

    def get_parent_counts(self) -> List[int]:
        return [obj.get_parent_count() for obj in self.objects]

    def get_summary(self) -> Dict[str, Any]:
        return {
            "objects": self.get_object_count(),
            "events": Stats(self.get_event_counts()),
            "metrics": Stats(self.get_metric_counts()),
            "properties": Stats(self.get_property_counts()),
            "parents": Stats(self.get_parent_counts()),
            "children": Stats(self.get_children_counts()),
        }


class LongObjectTypeStatistics:
    def __init__(self, long_run_duration: float) -> None:
        self.long_run_duration = long_run_duration
        self.objects_stats = UniqueObjectTypeStatistics()
        self.metrics_stats = UniqueObjectTypeStatistics()
        self.properties_stats = UniqueObjectTypeStatistics()
        self.events_stats = UniqueObjectTypeStatistics()
        self.relationships_stats = UniqueObjectTypeStatistics()
        self.string_property_values_stats = UniqueObjectTypeStatistics()

    def add(self, _object: ObjectTypeStatistics) -> None:
        self.objects_stats.add(_object.get_unique_objects(), _object.get_object_count())
        self.metrics_stats.add(_object.get_unique_metrics(), _object.get_metric_count())
        self.properties_stats.add(
            _object.get_unique_properties(), _object.get_property_count()
        )
        self.events_stats.add(_object.get_unique_events(), _object.get_event_count())
        unique_relationships = _object.get_unique_relationships()
        self.relationships_stats.add(unique_relationships, len(unique_relationships))
        self.string_property_values_stats.add(
            _object.get_unique_string_property_values(), 0
        )

    def get_growth_rates(self) -> List[str]:
        return [
            f"{self.objects_growth_rate:.2f} %",
            f"{self.metrics_growth_rate:.2f} %",
            f"{self.properties_growth_rate:.2f} %",
            f"{self.string_properties_growth_rate:.2f} %",
            f"{self.events_growth_rate:.2f} %",
            f"{self.relationships_growth_rate:.2f} %",
        ]

    def get_summary(self) -> Dict[str, Any]:
        return {
            "objects": LongRunStats(self.objects_stats.counts),
            "events": LongRunStats(self.events_stats.counts),
            "metrics": LongRunStats(self.metrics_stats.counts),
            "properties": LongRunStats(self.properties_stats.counts),
            "relationships": LongRunStats(self.relationships_stats.counts),
        }

    @LazyAttribute
    def objects_growth_rate(self) -> float:
        hours = self.long_run_duration / 3600
        return get_growth_rate(
            self.objects_stats.data_points[0], self.objects_stats.data_points[-1], hours
        )

    @LazyAttribute
    def metrics_growth_rate(self) -> float:
        hours = self.long_run_duration / 3600
        return get_growth_rate(
            self.metrics_stats.data_points[0], self.metrics_stats.data_points[-1], hours
        )

    @LazyAttribute
    def properties_growth_rate(self) -> float:
        hours = self.long_run_duration / 3600
        return get_growth_rate(
            self.properties_stats.data_points[0],
            self.properties_stats.data_points[-1],
            hours,
        )

    @LazyAttribute
    def property_values_growth_rate(self) -> float:
        hours = self.long_run_duration / 3600
        return get_growth_rate(
            self.string_property_values_stats.data_points[0],
            self.string_property_values_stats.data_points[-1],
            hours,
        )

    @LazyAttribute
    def string_properties_growth_rate(self) -> float:
        hours = self.long_run_duration / 3600
        return get_growth_rate(
            self.string_property_values_stats.data_points[0],
            self.string_property_values_stats.data_points[-1],
            hours,
        )

    @LazyAttribute
    def events_growth_rate(self) -> float:
        hours = self.long_run_duration / 3600
        return get_growth_rate(
            self.events_stats.data_points[0], self.events_stats.data_points[-1], hours
        )

    @LazyAttribute
    def relationships_growth_rate(self) -> float:
        hours = self.long_run_duration / 3600
        return get_growth_rate(
            self.relationships_stats.data_points[0],
            self.relationships_stats.data_points[-1],
            hours,
        )


class LongCollectionStatistics:
    def __init__(
        self,
        collection_bundle_list: List[CollectionBundle],
        collection_interval: float,
        long_run_duration: float,
    ) -> None:
        self.collection_interval = collection_interval
        self.long_run_duration = long_run_duration
        # This is a duplicated from LongCollectionBundle
        self.collection_bundles: List[CollectionBundle] = list()
        self.total_number_of_collections = len(collection_bundle_list)
        self.long_object_type_statistics: Dict[
            ObjectType, LongObjectTypeStatistics
        ] = defaultdict(lambda: LongObjectTypeStatistics(long_run_duration))
        for collection_bundle in collection_bundle_list:
            self.add(collection_bundle)

    def add(self, collection_bundle: CollectionBundle) -> None:
        self.collection_bundles.append(collection_bundle)
        statistics = collection_bundle.get_collection_statistics()
        if statistics:
            for object_type, object_type_stat in statistics.obj_type_statistics.items():
                self.long_object_type_statistics[object_type].add(object_type_stat)

    def __str__(self) -> str:
        headers = [
            "Object Type",
            "Object Growth",
            "Metric Growth",
            "Property Growth",
            "Property Values Growth",
            "Event Growth",
            "Relationship Growth",
        ]
        data = []
        for (
            object_type,
            obj_type_statistics,
        ) in self.long_object_type_statistics.items():
            data.append([object_type, *obj_type_statistics.get_growth_rates()])
        growth_table = str(Table(headers, data))

        headers = [
            "Object Type",
            "Count",
            "Metrics",
            "Properties",
            "Events",
            "Relationships",
        ]
        data = []
        for (
            object_type,
            obj_type_statistics,
        ) in self.long_object_type_statistics.items():
            obj_summary = obj_type_statistics.get_summary()
            data.append(
                [
                    object_type,
                    obj_summary["objects"],
                    obj_summary["metrics"],
                    obj_summary["properties"],
                    obj_summary["events"],
                    obj_summary["relationships"],
                ]
            )
        obj_table = str(Table(headers, data))

        headers = ["Collection", "Duration", *ContainerStats.get_summary_headers()]
        data = []
        failed_collections = list()
        longer_collections = list()
        # TODO: move this logic when doing UI reformatting
        for collection_stat in self.collection_bundles:
            number = str(collection_stat.collection_number)
            if collection_stat.failed():
                number = f"{number} (failed)"
                failed_collections.append(collection_stat)

                # If the connection timeout then we should also include it in the longer_collections
                if (
                    "408" in collection_stat.get_failure_message()
                    and collection_stat.duration > self.collection_interval
                ):
                    longer_collections.append(collection_stat)

            elif collection_stat.duration > self.collection_interval:
                number = f"{number} (longer than collection interval)"
                longer_collections.append(collection_stat)
            if collection_stat.container_statistics:
                data.append(
                    [
                        number,
                        f"{collection_stat.duration:.2f} s",
                        *collection_stat.container_statistics.get_summary(),
                    ]
                )
            else:
                data.append([number, f"{collection_stat.duration:.2f} s", []])
        collection_table = str(Table(headers, data))

        summary = (
            "Long Collection summary:\n\n"
            + obj_table
            + "\n"
            + growth_table
            + "\n"
            + collection_table
        )
        if len(failed_collections):
            headers = ["Collection", "Failure Reason"]
            data = []
            for failed_collection in failed_collections:
                data.append(
                    [
                        failed_collection.collection_number,
                        failed_collection.get_failure_message(),
                    ]
                )

            summary += "\n" + str(Table(headers, data))
            summary += "\n" + f"{len(failed_collections)} failed collections"
        if len(longer_collections):
            summary += (
                "\n" + f"{len(longer_collections)} took longer than collection interval"
            )

        return summary

    def __repr__(self) -> str:
        return str(self.__dict__)


class CollectionStatistics:
    def __init__(self, json: Dict) -> None:
        self.obj_type_statistics: Dict = defaultdict(lambda: ObjectTypeStatistics())
        self.obj_statistics: Dict = {}
        self.rel_statistics: Dict = defaultdict(lambda: 0)
        self.get_counts(json)

    def get_counts(self, json: Dict) -> None:
        for obj in json.get("result", []):
            obj_id = _get_object_id(obj.get("key"))
            if obj_id:
                stats = ObjectStatistics(obj)
                self.obj_statistics[obj_id] = stats
                self.obj_type_statistics[obj_id.objectKind].add_object(stats)
        for rel in json.get("relationships", []):
            parent_dict = rel.get("parent")
            parent = _get_object_id(parent_dict)
            children = rel.get("children", [])
            for child_dict in children:
                child = _get_object_id(child_dict)
                if child and parent:
                    key = (parent.objectKind, child.objectKind)
                    self.rel_statistics[key] += 1
                    if parent not in self.obj_statistics:
                        self.obj_statistics[parent] = ObjectStatistics(
                            {"key": parent_dict}
                        )
                    self.obj_statistics[parent].add_child(child)
                    if child not in self.obj_statistics:
                        self.obj_statistics[child] = ObjectStatistics(
                            {"key": child_dict}
                        )
                    self.obj_statistics[child].add_parent(parent)

    def __repr__(self) -> str:
        headers = [
            "Object Type",
            "Count",
            "Metrics",
            "Properties",
            "Events",
            "Parents",
            "Children",
        ]
        data = []

        for stats in list(self.obj_type_statistics.values()):
            summary = stats.get_summary()
            data.append(
                [
                    stats.object_type,
                    summary["objects"],
                    summary["metrics"],
                    summary["properties"],
                    summary["events"],
                    summary["parents"],
                    summary["children"],
                ]
            )
        obj_table = str(Table(headers, data))

        headers = ["Parent Type", "Child Type", "Count"]
        data = []
        for (parent_object_type, child_object_type), count in list(
            self.rel_statistics.items()
        ):
            data.append([parent_object_type, child_object_type, count])
        rel_table = str(Table(headers, data))

        return "Collection summary: \n\n" + obj_table + "\n" + rel_table
