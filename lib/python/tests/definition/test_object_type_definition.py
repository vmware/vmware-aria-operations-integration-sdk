#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import pytest

from vrops.definition.exceptions import KeyException, DuplicateKeyException
from vrops.definition.object_type import ObjectType
from vrops.definition.parameter import IntParameter, StringParameter


def test_object_type_definition_default_label():
    key = "key"
    definition = ObjectType(key)
    assert definition.label == key


def test_missing_object_type_key_raises_exception():
    with pytest.raises(KeyException):
        ObjectType(key=None)


def test_blank_object_type_key_raises_exception():
    with pytest.raises(KeyException):
        ObjectType(key="  \t")


def test_object_type_key_with_incorrect_type_raises_exception():
    with pytest.raises(KeyException):
        ObjectType(key=9)


def test_adapter_definition_label():
    key = "key"
    label = "Label"
    definition = ObjectType(key, label)
    assert definition.label == label


def test_identifier_order():
    definition = ObjectType("test")
    definition.define_string_identifier("id1")
    definition.define_string_identifier("id2")
    identifiers = definition.to_json()["identifiers"]
    param1 = list(filter(lambda i: i["key"] == "id1", identifiers))[0]
    param2 = list(filter(lambda i: i["key"] == "id2", identifiers))[0]
    assert param1["display_order"] < param2["display_order"]


def test_duplicate_identifier_keys_not_allowed():
    definition = ObjectType("test")
    definition.define_string_identifier("id1")
    with pytest.raises(DuplicateKeyException):
        definition.define_enum_identifier("id1", ["item1", "item2"])


def test_define_string_identifier():
    definition = ObjectType("test")
    definition.define_string_identifier("A", "B", True, False, "C")
    assert definition.identifiers["A"].to_json() == {
        "key": "A",
        "label": "B",
        "required": True,
        "ident_type": 2,
        "enum": False,
        "description": None,
        "default": "C",
        "display_order": 0,
        "type": "string",
        "length": None
    }


def test_define_int_identifier():
    definition = ObjectType("test")
    definition.define_int_identifier("A", "B", False, True, 9)
    assert definition.identifiers["A"].to_json() == {
        "key": "A",
        "label": "B",
        "required": False,
        "ident_type": 1,
        "enum": False,
        "description": None,
        "default": 9,
        "display_order": 0,
        "type": "integer",
        "length": None
    }


def test_define_enum_identifier():
    definition = ObjectType("test")
    definition.define_enum_identifier("A", ["B", "C"], "D", False, False, "E")
    assert definition.identifiers["A"].to_json() == {
        "key": "A",
        "label": "D",
        "required": False,
        "ident_type": 2,
        "enum": True,
        "enum_values": ["B", "C", "E"],
        "description": None,
        "default": 9,
        "display_order": 0,
        "type": "string",
        "length": None
    }


def test_add_identifiers():
    definition = ObjectType("test")
    assert len(definition.identifiers) == 0
    definition.add_identifiers([
        IntParameter("key1"),
        StringParameter("key2")
    ])
    assert "key1" in definition.identifiers
    assert "key2" in definition.identifiers
    assert len(definition.identifiers) == 2


def test_add_identifier():
    definition = ObjectType("test")
    assert len(definition.identifiers) == 0
    definition.add_identifier(IntParameter("key1"))
    assert "key1" in definition.identifiers
    assert len(definition.identifiers) == 1
