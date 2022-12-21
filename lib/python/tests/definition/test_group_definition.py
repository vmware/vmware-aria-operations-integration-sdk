#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import pytest
from _pytest.fixtures import SubRequest
from aria.ops.definition.adapter_definition import AdapterDefinition
from aria.ops.definition.attribute import MetricAttribute
from aria.ops.definition.attribute import PropertyAttribute
from aria.ops.definition.exceptions import DuplicateKeyException
from aria.ops.definition.exceptions import KeyException
from aria.ops.definition.group import Group
from aria.ops.definition.group import GroupType
from aria.ops.definition.object_type import ObjectType
from aria.ops.definition.units import Units


def test_group_definition_default_label() -> None:
    key = "key"
    group = Group(key)
    assert group.label == key


def test_group_definition_custom_label() -> None:
    label = "Label"
    group = Group("key", label)
    assert group.label == label


def test_missing_group_key_raises_exception() -> None:
    with pytest.raises(KeyException):
        Group(key=None)


def test_invalid_group_key_type_raises_exception() -> None:
    with pytest.raises(KeyException):
        Group(key=5)


def test_empty_group_key_raises_exception() -> None:
    with pytest.raises(KeyException):
        Group(key="")


def test_blank_group_key_raises_exception() -> None:
    with pytest.raises(KeyException):
        Group(key="\n ")


# The following tests apply to all classes that extends GroupType, so we'll run each test
# for each of those classes:
@pytest.fixture(params=[Group, AdapterDefinition, ObjectType])  # type: ignore
def group(request: SubRequest) -> GroupType:
    return request.param("parent")


def test_define_group(group: GroupType) -> None:
    group.define_group("A", "B")
    assert len(group.groups) == 1
    assert group.groups["A"].to_json() == {
        "key": "A",
        "label": "B",
        "attributes": [],
        "groups": [],
        "instanced": False,
        "instance_required": True,
    }


def test_define_instanced_group(group: GroupType) -> None:
    group.define_instanced_group("A", "B", False)
    assert len(group.groups) == 1
    assert group.groups["A"].to_json() == {
        "key": "A",
        "label": "B",
        "attributes": [],
        "groups": [],
        "instanced": True,
        "instance_required": False,
    }


def test_duplicate_group_keys_not_allowed(group: GroupType) -> None:
    group.define_group("child")
    with pytest.raises(DuplicateKeyException):
        group.define_instanced_group("child")


def test_add_groups(group: GroupType) -> None:
    child1 = Group("A", "B", True, False)
    child2 = Group("C", "D", False, True)
    group.add_groups([child1, child2])
    assert len(group.groups) == 2
    assert group.groups["A"].to_json() == {
        "key": "A",
        "label": "B",
        "attributes": [],
        "groups": [],
        "instanced": True,
        "instance_required": False,
    }
    assert group.groups["C"].to_json() == {
        "key": "C",
        "label": "D",
        "attributes": [],
        "groups": [],
        "instanced": False,
        "instance_required": True,
    }


def test_add_group(group: GroupType) -> None:
    child1 = Group("A", "B", True, True)
    group.add_group(child1)
    assert len(group.groups) == 1
    assert group.groups["A"].to_json() == {
        "key": "A",
        "label": "B",
        "attributes": [],
        "groups": [],
        "instanced": True,
        "instance_required": True,
    }


def test_duplicate_attribute_keys_not_allowed(group: GroupType) -> None:
    group.define_metric("child")
    with pytest.raises(DuplicateKeyException):
        group.define_string_property("child")


def test_define_integer_metric(group: GroupType) -> None:
    group.define_metric("A", "B", Units.DATA_SIZE.BYTE, True, True, True, True, True)
    assert len(group.attributes) == 1
    assert group.attributes["A"].to_json() == {
        "key": "A",
        "label": "B",
        "unit": "byte",
        "is_rate": False,  # We set is_rate to 'True' in the constructor, but the non-rate unit 'Byte' takes precedence
        "is_discrete": True,
        "data_type": "integer",  # derived from is_discrete = True
        "is_kpi": True,
        "is_impact": True,
        "is_key_attribute": True,
        "is_property": False,
        "dashboard_order": 0,
    }


def test_define_float_metric(group: GroupType) -> None:
    group.define_metric(
        "A", "B", Units.RATIO.PERCENT, False, False, False, False, False
    )
    assert len(group.attributes) == 1
    assert group.attributes["A"].to_json() == {
        "key": "A",
        "label": "B",
        "unit": "percent",
        "is_rate": False,
        "is_discrete": False,
        "data_type": "float",  # derived from is_discrete = False
        "is_kpi": False,
        "is_impact": False,
        "is_key_attribute": False,
        "is_property": False,
        "dashboard_order": 0,
    }


def test_define_string_property(group: GroupType) -> None:
    group.define_string_property("A", "B", None, False, True, True, True, True)
    assert len(group.attributes) == 1
    assert group.attributes["A"].to_json() == {
        "key": "A",
        "label": "B",
        "unit": None,
        "is_rate": False,
        "is_discrete": True,
        "data_type": "string",
        "is_kpi": True,
        "is_impact": True,
        "is_key_attribute": True,
        "is_property": True,
        "dashboard_order": 0,
    }


def test_define_numeric_property_1(group: GroupType) -> None:
    group.define_numeric_property(
        "A", "B", Units.MISC.RACK_UNIT, False, True, True, True, True
    )
    assert len(group.attributes) == 1
    assert group.attributes["A"].to_json() == {
        "key": "A",
        "label": "B",
        "unit": "rackunit",
        "is_rate": False,
        "is_discrete": True,
        "data_type": "integer",
        "is_kpi": True,
        "is_impact": True,
        "is_key_attribute": True,
        "is_property": True,
        "dashboard_order": 0,
    }


def test_define_numeric_property_2(group: GroupType) -> None:
    group.define_numeric_property(
        "A", "B", Units.FREQUENCY.GIGAHERTZ, False, False, True, True, True
    )
    assert len(group.attributes) == 1
    assert group.attributes["A"].to_json() == {
        "key": "A",
        "label": "B",
        "unit": "gigahertz",
        "is_rate": True,
        "is_discrete": False,
        "data_type": "float",
        "is_kpi": True,
        "is_impact": True,
        "is_key_attribute": True,
        "is_property": True,
        "dashboard_order": 0,
    }


def test_add_attributes(group: GroupType) -> None:
    attribute1 = PropertyAttribute("key1")
    attribute2 = MetricAttribute("key2")
    group.add_attributes([attribute1, attribute2])
    assert len(group.attributes) == 2


def test_add_attribute(group: GroupType) -> None:
    attribute1 = PropertyAttribute("key1")
    group.add_attribute(attribute1)
    assert len(group.attributes) == 1
