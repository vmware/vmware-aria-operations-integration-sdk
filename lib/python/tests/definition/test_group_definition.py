#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import pytest

from vrops.definition.adapter_definition import AdapterDefinition
from vrops.definition.attribute import PropertyAttribute, MetricAttribute
from vrops.definition.exceptions import KeyException, DuplicateKeyException
from vrops.definition.group import Group
from vrops.definition.object_type import ObjectType
from vrops.definition.units import Units


def test_group_definition_default_label():
    key = "key"
    group = Group(key)
    assert group.label == key


def test_group_definition_custom_label():
    label = "Label"
    group = Group("key", label)
    assert group.label == label


def test_missing_group_key_raises_exception():
    with pytest.raises(KeyException):
        Group(key=None)


def test_invalid_group_key_type_raises_exception():
    with pytest.raises(KeyException):
        Group(key=5)


def test_empty_group_key_raises_exception():
    with pytest.raises(KeyException):
        Group(key="")


def test_blank_group_key_raises_exception():
    with pytest.raises(KeyException):
        Group(key="\n ")


def test_define_group(group):
    group.define_group("A", "B")
    assert len(group.groups) == 1
    assert group.groups["A"].to_json() == {
        "key": "A",
        "label": "B",
        "attributes": [],
        "groups": [],
        "instanced": False,
        "instance_required": True
    }


# The following tests apply to all classes that extends GroupType, so we'll run each test
# for each of those classes:
@pytest.fixture(params=[Group, AdapterDefinition, ObjectType])
def group(request):
    return request.param("parent")


def test_define_instanced_group(group):
    group.define_instanced_group("A", "B", False)
    assert len(group.groups) == 1
    assert group.groups["A"].to_json() == {
        "key": "A",
        "label": "B",
        "attributes": [],
        "groups": [],
        "instanced": True,
        "instance_required": False
    }


def test_duplicate_group_keys_not_allowed(group):
    group.define_group("child")
    with pytest.raises(DuplicateKeyException):
        group.define_instanced_group("child")


def test_add_groups(group):
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
        "instance_required": False
    }
    assert group.groups["C"].to_json() == {
        "key": "C",
        "label": "D",
        "attributes": [],
        "groups": [],
        "instanced": False,
        "instance_required": True
    }


def test_add_group(group):
    child1 = Group("A", "B", True, True)
    group.add_group(child1)
    assert len(group.groups) == 1
    assert group.groups["A"].to_json() == {
        "key": "A",
        "label": "B",
        "attributes": [],
        "groups": [],
        "instanced": True,
        "instance_required": True
    }


def test_define_integer_metric(group):
    group.define_metric("A", "B", Units.DATA_SIZE.BYTE, True, True, True, True, "multinomial", True)
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
        "dt_type": "multinomial",
        "is_key_attribute": True,
        "is_property": False,
        "dashboard_order": 0
    }


def test_define_float_metric(group):
    group.define_metric("A", "B", Units.RATIO.PERCENT, False, False, False, False, "polynomial", False)
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
        "dt_type": "polynomial",
        "is_key_attribute": False,
        "is_property": False,
        "dashboard_order": 0
    }


def test_define_string_property(group):
    group.define_string_property("A", "B", None, False, True, True, True, "multinomial", True)
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
        "dt_type": "multinomial",
        "is_key_attribute": True,
        "is_property": True,
        "dashboard_order": 0
    }


def test_define_numeric_property_1(group):
    group.define_numeric_property("A", "B", Units.MISC.RACK_UNIT, False, True, True, True, "", True)
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
        "dt_type": "",
        "is_key_attribute": True,
        "is_property": True,
        "dashboard_order": 0
    }


def test_define_numeric_property_2(group):
    group.define_numeric_property("A", "B", Units.FREQUENCY.GIGAHERTZ, False, False, True, True, "polynomial", True)
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
        "dt_type": "polynomial",
        "is_key_attribute": True,
        "is_property": True,
        "dashboard_order": 0
    }


def test_add_attributes(group):
    attribute1 = PropertyAttribute("key1")
    attribute2 = MetricAttribute("key2")
    group.add_attributes([attribute1, attribute2])
    assert len(group.attributes) == 2


def test_add_attribute(group):
    attribute1 = PropertyAttribute("key1")
    group.add_attribute(attribute1)
    assert len(group.attributes) == 1

