#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import copy
from typing import Any
from typing import Dict

from aria.ops.definition.adapter_definition import AdapterDefinition
from aria.ops.event import Criticality
from aria.ops.result import CollectResult
from aria.ops.result import RelationshipUpdateModes

one_object_base_result: Dict[str, Any] = {
    "nonExistingObjects": [],
    "relationships": [],
    "result": [
        {
            "events": [],
            "key": {
                "adapterKind": "Adapter",
                "identifiers": [],
                "name": "Name",
                "objectKind": "Object",
            },
            "metrics": [],
            "properties": [],
        }
    ],
}

two_object_base_result: Dict[str, Any] = {
    "nonExistingObjects": [],
    "relationships": [],
    "result": [
        {
            "events": [],
            "key": {
                "adapterKind": "Adapter",
                "identifiers": [],
                "name": "Name1",
                "objectKind": "Object",
            },
            "metrics": [],
            "properties": [],
        },
        {
            "events": [],
            "key": {
                "adapterKind": "Adapter",
                "identifiers": [],
                "name": "Name2",
                "objectKind": "Object",
            },
            "metrics": [],
            "properties": [],
        },
    ],
}


def test_get_json_1_object() -> None:
    result = CollectResult()
    result.object("Adapter", "Object", "Name")
    assert result.get_json() == one_object_base_result


def test_get_json_1_object_with_metric() -> None:
    result = CollectResult()
    obj = result.object("Adapter", "Object", "Name")
    obj.with_metric("metric", 1, 1000)
    expected_result = copy.deepcopy(one_object_base_result)
    expected_result["result"][0]["metrics"] = [
        {"key": "metric", "numberValue": 1.0, "timestamp": 1000}
    ]
    assert result.get_json() == expected_result


def test_get_json_1_object_with_numeric_property() -> None:
    result = CollectResult()
    obj = result.object("Adapter", "Object", "Name")
    obj.with_property("property", 1, 1000)
    expected_result = copy.deepcopy(one_object_base_result)
    expected_result["result"][0]["properties"] = [
        {"key": "property", "numberValue": 1.0, "timestamp": 1000}
    ]
    assert result.get_json() == expected_result


def test_get_json_1_object_with_string_property() -> None:
    result = CollectResult()
    obj = result.object("Adapter", "Object", "Name")
    obj.with_property("property", "string", 1000)
    expected_result = copy.deepcopy(one_object_base_result)
    expected_result["result"][0]["properties"] = [
        {"key": "property", "stringValue": "string", "timestamp": 1000}
    ]
    assert result.get_json() == expected_result


def test_get_json_1_object_with_event() -> None:
    result = CollectResult()
    obj = result.object("Adapter", "Object", "Name")
    obj.with_event("event message", Criticality.CRITICAL)
    expected_result = copy.deepcopy(one_object_base_result)
    expected_result["result"][0]["events"] = [
        {
            "autoCancel": False,
            "cancelWaitCycle": 3,
            "criticality": 4,
            "message": "event message",
            "watchWaitCycle": 1,
        }
    ]
    assert result.get_json() == expected_result


def test_get_json_2_objects() -> None:
    result = CollectResult()
    result.object("Adapter", "Object", "Name1")
    result.object("Adapter", "Object", "Name2")
    assert result.get_json() == two_object_base_result


def test_get_json_2_objects_one_external() -> None:
    result = CollectResult(target_definition=AdapterDefinition("Adapter"))
    result.object("Adapter", "Object", "Name")
    result.object("Adapter1", "Object", "Name1")
    # There are no metrics, properties, or events on external 'Adapter1' type,
    # so we don't include it
    assert result.get_json() == one_object_base_result


def test_get_json_2_objects_one_external_with_metric() -> None:
    result = CollectResult(target_definition=AdapterDefinition("Adapter"))
    result.object("Adapter", "Object", "Name1")
    ext_obj = result.object("Adapter1", "Object", "Name2")
    ext_obj.with_metric("appended_metric", 1, 1000)
    expected_result = copy.deepcopy(two_object_base_result)
    # Because we added a metric to the external kind, it will be included
    expected_result["result"][1]["key"]["adapterKind"] = "Adapter1"
    expected_result["result"][1]["metrics"] = [
        {"key": "appended_metric", "numberValue": 1.0, "timestamp": 1000}
    ]
    assert result.get_json() == expected_result


def test_get_json_2_objects_relationships_none() -> None:
    # 'NONE' will not set relationships for any object
    result = CollectResult()
    result.update_relationships = RelationshipUpdateModes.NONE
    obj1 = result.object("Adapter", "Object", "Name1")
    obj2 = result.object("Adapter", "Object", "Name2")
    assert result.get_json() == two_object_base_result


def test_get_json_2_objects_relationships_none1() -> None:
    # 'NONE' will not set relationships for any object, even if there are relationships
    result = CollectResult()
    result.update_relationships = RelationshipUpdateModes.NONE
    obj1 = result.object("Adapter", "Object", "Name1")
    obj2 = result.object("Adapter", "Object", "Name2")
    obj1.add_child(obj2)
    assert result.get_json() == two_object_base_result


def test_get_json_2_objects_relationships_all() -> None:
    result = CollectResult()
    # 'ALL' will set relationships for each object
    result.update_relationships = RelationshipUpdateModes.ALL
    obj1 = result.object("Adapter", "Object", "Name1")
    obj2 = result.object("Adapter", "Object", "Name2")
    obj1.add_child(obj2)
    expected_result = copy.deepcopy(two_object_base_result)
    expected_result["relationships"] = [
        {
            "children": [
                {
                    "adapterKind": "Adapter",
                    "identifiers": [],
                    "name": "Name2",
                    "objectKind": "Object",
                }
            ],
            "parent": {
                "adapterKind": "Adapter",
                "identifiers": [],
                "name": "Name1",
                "objectKind": "Object",
            },
        },
        {
            "children": [],
            "parent": {
                "adapterKind": "Adapter",
                "identifiers": [],
                "name": "Name2",
                "objectKind": "Object",
            },
        },
    ]
    assert result.get_json() == expected_result


def test_get_json_2_objects_relationships_all1() -> None:
    result = CollectResult()
    # 'ALL' will set relationships for each object, even if there are no relationships
    result.update_relationships = RelationshipUpdateModes.ALL
    obj1 = result.object("Adapter", "Object", "Name1")
    obj2 = result.object("Adapter", "Object", "Name2")
    expected_result = copy.deepcopy(two_object_base_result)
    expected_result["relationships"] = [
        {
            "children": [],
            "parent": {
                "adapterKind": "Adapter",
                "identifiers": [],
                "name": "Name1",
                "objectKind": "Object",
            },
        },
        {
            "children": [],
            "parent": {
                "adapterKind": "Adapter",
                "identifiers": [],
                "name": "Name2",
                "objectKind": "Object",
            },
        },
    ]
    assert result.get_json() == expected_result


def test_get_json_2_objects_relationships_auto() -> None:
    result = CollectResult()
    # 'AUTO' will not set relationships for any objects if all objects have no
    # relationships
    result.update_relationships = RelationshipUpdateModes.AUTO
    obj1 = result.object("Adapter", "Object", "Name1")
    obj2 = result.object("Adapter", "Object", "Name2")
    assert result.get_json() == two_object_base_result


def test_get_json_2_objects_relationships_auto1() -> None:
    result = CollectResult()
    # 'AUTO' will set relationships for all objects if any object has at least one
    # relationship
    result.update_relationships = RelationshipUpdateModes.AUTO
    obj1 = result.object("Adapter", "Object", "Name1")
    obj2 = result.object("Adapter", "Object", "Name2")
    obj1.add_child(obj2)

    expected_result = copy.deepcopy(two_object_base_result)
    expected_result["relationships"] = [
        {
            "children": [
                {
                    "adapterKind": "Adapter",
                    "identifiers": [],
                    "name": "Name2",
                    "objectKind": "Object",
                }
            ],
            "parent": {
                "adapterKind": "Adapter",
                "identifiers": [],
                "name": "Name1",
                "objectKind": "Object",
            },
        },
        {
            "children": [],
            "parent": {
                "adapterKind": "Adapter",
                "identifiers": [],
                "name": "Name2",
                "objectKind": "Object",
            },
        },
    ]
    assert result.get_json() == expected_result


def test_get_json_2_objects_relationships_per_object() -> None:
    result = CollectResult()
    # 'PER_OBJECT' will not set relationships for any objects unless they have
    # children
    result.update_relationships = RelationshipUpdateModes.PER_OBJECT
    obj1 = result.object("Adapter", "Object", "Name1")
    obj2 = result.object("Adapter", "Object", "Name2")
    assert result.get_json() == two_object_base_result


def test_get_json_2_objects_relationships_per_object1() -> None:
    result = CollectResult()
    # 'PER_OBJECT' will set relationships for any objects that have children
    result.update_relationships = RelationshipUpdateModes.PER_OBJECT
    obj1 = result.object("Adapter", "Object", "Name1")
    obj2 = result.object("Adapter", "Object", "Name2")
    obj1.add_child(obj2)

    expected_result = copy.deepcopy(two_object_base_result)
    expected_result["relationships"] = [
        {
            "children": [
                {
                    "adapterKind": "Adapter",
                    "identifiers": [],
                    "name": "Name2",
                    "objectKind": "Object",
                }
            ],
            "parent": {
                "adapterKind": "Adapter",
                "identifiers": [],
                "name": "Name1",
                "objectKind": "Object",
            },
        }
    ]
    assert result.get_json() == expected_result


def test_get_json_2_objects_relationships_per_object2() -> None:
    result = CollectResult()
    # 'PER_OBJECT' will only set no relationships on an object if they have explicitly
    # added no children
    result.update_relationships = RelationshipUpdateModes.PER_OBJECT
    obj1 = result.object("Adapter", "Object", "Name1")
    obj2 = result.object("Adapter", "Object", "Name2")
    obj1.add_child(obj2)
    obj2.add_children([])

    expected_result = copy.deepcopy(two_object_base_result)
    expected_result["relationships"] = [
        {
            "children": [
                {
                    "adapterKind": "Adapter",
                    "identifiers": [],
                    "name": "Name2",
                    "objectKind": "Object",
                }
            ],
            "parent": {
                "adapterKind": "Adapter",
                "identifiers": [],
                "name": "Name1",
                "objectKind": "Object",
            },
        },
        {
            "children": [],
            "parent": {
                "adapterKind": "Adapter",
                "identifiers": [],
                "name": "Name2",
                "objectKind": "Object",
            },
        },
    ]
    assert result.get_json() == expected_result
