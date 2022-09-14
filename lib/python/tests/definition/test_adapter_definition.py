#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import pytest

from vrops.definition.adapter_definition import AdapterDefinition, KeyException


def test_adapter_definition_default_label():
    key = "key"
    definition = AdapterDefinition(key)
    assert definition.label == key


def test_missing_adapter_key_raises_exception():
    with pytest.raises(KeyException):
        definition = AdapterDefinition(key=None)


def test_invalid_type_adapter_key_raises_exception():
    with pytest.raises(KeyException):
        definition = AdapterDefinition(key=5)


def test_empty_adapter_key_raises_exception():
    with pytest.raises(KeyException):
        definition = AdapterDefinition(key="")


def test_blank_adapter_key_raises_exception():
    with pytest.raises(KeyException):
        definition = AdapterDefinition(key="\n ")


def test_leading_digit_adapter_key_raises_exception():
    with pytest.raises(KeyException):
        definition = AdapterDefinition(key="6key")


def test_containing_whitespace_adapter_key_raises_exception():
    with pytest.raises(KeyException) as ke:
        definition = AdapterDefinition(key="ke\ty")
    assert str(ke.value) == "Adapter key cannot contain whitespace."


def test_complex_valid_adapter_key():
    try:
        definition = AdapterDefinition(key="This_15_a_valid_KEY")
    except KeyException as e:
        assert e is False


def test_adapter_definition_label():
    key = "key"
    label = "Label"
    definition = AdapterDefinition(key, label)
    assert definition.label == label


def test_adapter_definition_default_ai_key():
    key = "key"
    definition = AdapterDefinition(key)
    assert definition.adapter_instance_key == f"{key}_adapter_instance"


def test_adapter_definition_default_ai_label():
    key = "key"
    definition = AdapterDefinition(key)
    assert definition.adapter_instance_label == f"{definition.label} Adapter Instance"


def test_adapter_definition_default_ai_label_2():
    key = "key"
    label = "Label"
    definition = AdapterDefinition(key, label)
    assert definition.adapter_instance_label == f"{definition.label} Adapter Instance"


def test_parameter_order():
    definition = AdapterDefinition("key")
    definition.string_parameter("param1")
    definition.string_parameter("param2")
    identifiers = definition.to_json()["adapter_instance"]["identifiers"]
    param1 = list(filter(lambda i: i["key"] == "param1", identifiers))[0]
    param2 = list(filter(lambda i: i["key"] == "param2", identifiers))[0]
    assert param1["display_order"] < param2["display_order"]


def test_enum_default_included():
    definition = AdapterDefinition("key")
    definition.enum_parameter("param1", values=["Item1", "Item2"], default="Item1")
    identifiers = definition.to_json()["adapter_instance"]["identifiers"]
    param1 = list(filter(lambda i: i["key"] == "param1", identifiers))[0]
    assert len(param1["enum_values"]) == 2


def test_enum_default_not_included():
    definition = AdapterDefinition("key")
    definition.enum_parameter("param1", values=["Item1", "Item2"], default="Item3")
    identifiers = definition.to_json()["adapter_instance"]["identifiers"]
    param1 = list(filter(lambda i: i["key"] == "param1", identifiers))[0]
    assert len(param1["enum_values"]) == 3
