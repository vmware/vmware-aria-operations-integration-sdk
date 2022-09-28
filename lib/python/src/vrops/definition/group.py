#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from abc import ABC
from collections import OrderedDict

from vrops.definition.attribute import PropertyAttribute, MetricAttribute


class GroupType(ABC):
    # This is only an Abstract Base Class so that it isn't initialized as a standalone object
    def __init__(self):
        self.attributes = OrderedDict()
        self.groups = OrderedDict()

    def group(self, key: str, label: str) -> Group:
        group = Group(key, label)
        self.groups[key] = group
        return group

    def instanced_group(self, key: str, label: str, instance_required: bool = True) -> Group:
        group = Group(key, label, instanced=True, instance_required=instance_required)
        self.groups[key] = group
        return group

    def metric(self, key, *args, **kwargs) -> GroupType:
        metric = MetricAttribute(key, *args, **kwargs, dashboard_order=len(self.attributes))
        self.attributes[key] = metric
        return self

    def string_property(self, key, *args, **kwargs) -> GroupType:
        _property = PropertyAttribute(key, *args, **kwargs, dashboard_order=len(self.attributes), is_string=True)
        self.attributes[key] = _property
        return self

    def numeric_property(self, key, *args, **kwargs) -> GroupType:
        _property = PropertyAttribute(key, *args, **kwargs, dashboard_order=len(self.attributes), is_string=False)
        self.attributes[key] = _property
        return self

    def to_json(self):
        return {
            "attributes": [attribute.to_json() for attribute in self.attributes.values()],
            "groups": [group.to_json() for group in self.groups.values()]
        }


class Group(GroupType):
    def __init__(self, key: str, label: str, instanced: bool = False, instance_required: bool = True):
        self.key = key
        self.label = label
        self.instanced = instanced
        self.instance_required = instance_required
        super().__init__()

    def to_json(self):
        return {
            "key": self.key,
            "label": self.label,
            "instanced": self.instanced,
            "instance_required": self.instance_required
        } | super().to_json()
