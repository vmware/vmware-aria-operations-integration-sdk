#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from abc import ABC
from collections import OrderedDict

from vrops.definition.attribute import PropertyAttribute, MetricAttribute, Attribute
from vrops.definition.exceptions import DuplicateKeyException
from vrops.definition.units import Unit


class GroupType(ABC):
    # This is only an Abstract Base Class so that it isn't initialized as a standalone object
    def __init__(self):
        self.attributes = OrderedDict()
        self.groups = OrderedDict()

    def define_group(self, key: str, label: str) -> Group:
        """
        Create a new group that can hold attributes and subgroups.
        :param key: The key for the group.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :return: The created group.
        """
        group = Group(key, label)
        self.add_group(group)
        return group

    def define_instanced_group(self, key: str, label: str, instance_required: bool = True) -> Group:
        """
        Create a new group that can hold attributes and subgroups. This group can be 'instanced', with a value, so that
        its subgroups and attributes can appear multiple times, once for each instance value. For example, a group
        containing metrics for a network interface might be instanced for each discovered interface on the parent
        object.
        :param key: The key for the group.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param instance_required: If true, then this group must be created with an instance. Otherwise, it can be
        created both with and without an instance. Creating an instanced group without an instance can be done to
        provide a location for aggregate metrics across all instances, for example.
        :return: The created group.
        """
        group = Group(key, label, instanced=True, instance_required=instance_required)
        self.add_group(group)
        return group

    def add_groups(self, groups: list[Group]):
        """
        Adds a list of groups as subgroups of this group.
        :param groups: A list of groups.
        :return: None
        """
        for group in groups:
            self.add_group(group)

    def add_group(self, group: Group):
        """
        Adds a group as a subgroup of this group.
        :param group: A group.
        :return: None
        """
        key = group.key
        if key in self.groups:
            raise DuplicateKeyException(f"Group with key {key} already exists in {type(self)} {self.key}.")
        self.groups[key] = group

    def define_metric(self, key: str,
                      label: str = None,
                      unit: Unit = None,
                      is_rate: bool = False,
                      is_discrete: bool = False,
                      is_kpi: bool = False,
                      is_impact: bool = False,
                      dt_type: str = None,
                      is_key_attribute: bool = False) -> MetricAttribute:
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param unit: Specifies what unit this metric is returned in. This allows the UI to display the units in a
        consistent manner, and perform conversions when appropriate.
        :param is_rate: Declares this attribute as a rate (e.g., kilobytes per second). If a unit is specified, this
        will be set automatically. Otherwise, defaults to False.
        :param is_discrete: Declares that this attribute's range of values is discrete (integer) rather than continuous
        (floating point)
        :param is_kpi: If set, threshold breaches for this metric will be used in the calculation of the object's
        'Self - Health Score' metric, which can affect the 'Anomalies' Badge.
        :param is_impact: If set, this attribute will never be the 'root cause' of an issue. For example, it could be a
        proxy to a root cause, but not the root cause itself.
        :param dt_type: The type of algorithm to use for dynamic thresholding.
        :param is_key_attribute: True if the attribute should be shown in some object summary widgets in the UI.
        """
        metric = MetricAttribute(key, label, unit, is_rate, is_discrete, is_kpi, is_impact, dt_type, is_key_attribute,
                                 dashboard_order=len(self.attributes))
        self.add_attribute(metric)
        return metric

    def define_string_property(self, key: str,
                               label: str = None,
                               unit: Unit = None,
                               is_rate: bool = False,
                               is_discrete: bool = False,
                               is_kpi: bool = False,
                               is_impact: bool = False,
                               dt_type: str = None,
                               is_key_attribute: bool = False) -> PropertyAttribute:
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param unit: Specifies what unit this metric is returned in. This allows the UI to display the units in a
        consistent manner, and perform conversions when appropriate.
        :param is_rate: Declares this attribute as a rate (e.g., kilobytes per second). If a unit is specified, this
        will be set automatically. Otherwise, defaults to False.
        :param is_discrete: Declares that this attribute's range of values is discrete (integer) rather than continuous
        (floating point). Defaults to False, unless 'is_string' is set, in which case it will always be set to True.
        :param is_kpi: If set, threshold breaches for this metric will be used in the calculation of the object's
        'Self - Health Score' metric, which can affect the 'Anomalies' Badge.
        :param is_impact: If set, this attribute will never be the 'root cause' of an issue. For example, it could be a
        proxy to a root cause, but not the root cause itself.
        :param dt_type: The type of algorithm to use for dynamic thresholding.
        :param is_key_attribute: True if the attribute should be shown in some object summary widgets in the UI.
        """
        _property = PropertyAttribute(key, label, True, unit, is_rate, is_discrete, is_kpi, is_impact, dt_type,
                                      is_key_attribute, dashboard_order=len(self.attributes))
        self.add_attribute(_property)
        return _property

    def define_numeric_property(self, key: str,
                                label: str = None,
                                unit: Unit = None,
                                is_rate: bool = False,
                                is_discrete: bool = False,
                                is_kpi: bool = False,
                                is_impact: bool = False,
                                dt_type: str = None,
                                is_key_attribute: bool = False) -> PropertyAttribute:
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param unit: Specifies what unit this metric is returned in. This allows the UI to display the units in a
        consistent manner, and perform conversions when appropriate.
        :param is_rate: Declares this attribute as a rate (e.g., kilobytes per second). If a unit is specified, this
        will be set automatically. Otherwise, defaults to False.
        :param is_discrete: Declares that this attribute's range of values is discrete (integer) rather than continuous
        (floating point). Defaults to False, unless 'is_string' is set, in which case it will always be set to True.
        :param is_kpi: If set, threshold breaches for this metric will be used in the calculation of the object's
        'Self - Health Score' metric, which can affect the 'Anomalies' Badge.
        :param is_impact: If set, this attribute will never be the 'root cause' of an issue. For example, it could be a
        proxy to a root cause, but not the root cause itself.
        :param dt_type: The type of algorithm to use for dynamic thresholding.
        :param is_key_attribute: True if the attribute should be shown in some object summary widgets in the UI.
        """
        _property = PropertyAttribute(key, label, False, unit, is_rate, is_discrete, is_kpi, is_impact, dt_type,
                                      is_key_attribute, dashboard_order=len(self.attributes))
        self.add_attribute(_property)
        return _property

    def add_attributes(self, attributes: list[Attribute]):
        """
        Adds a list of attributes to this group.
        :param attributes: A list of attributes (metric or property definitions).
        :return: None
        """
        for attribute in attributes:
            self.add_attribute(attribute)

    def add_attribute(self, attribute: Attribute):
        """
        Adds an attribute to this group.
        :param attribute: An attribute (metric or property definition).
        :return: None
        """
        key = attribute.key
        if key in self.attributes:
            raise DuplicateKeyException(f"Group with key {key} already exists in {type(self)} {self.key}.")

        self.attributes[key] = attribute

    def to_json(self):
        return {
            "attributes": [attribute.to_json() for attribute in self.attributes.values()],
            "groups": [group.to_json() for group in self.groups.values()]
        }


class Group(GroupType):
    def __init__(self, key: str, label: str = None, instanced: bool = False, instance_required: bool = True):
        """
        Create a new group that can hold attributes and subgroups.
        :param key: The key for the group.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param instanced: If True, this group can be 'instanced' with a value, so that its subgroups and attributes can
        appear multiple times, once for each instance value. For example, a group containing
        metrics for a network interface might be instanced for each discovered interface on the parent object.
        :param instance_required: If true, then this group must be created with an instance. Otherwise, it can be
        created both with and without an instance. Creating an instanced group without an instance can be done to
        provide a location for aggregate metrics across all instances, for example. This does nothing if 'instanced' is
        False.
        """
        self.key = key
        self.label = label
        if label is None:
            self.label = key
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
