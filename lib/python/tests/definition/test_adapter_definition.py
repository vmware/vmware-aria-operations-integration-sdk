#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import pytest

from vrops.definition.adapter_definition import AdapterDefinition
from vrops.definition.exceptions import KeyException, DuplicateKeyException


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


def test_duplicate_parameter_keys_not_allowed():
    with pytest.raises(DuplicateKeyException) as dke:
        definition = AdapterDefinition("key")
        definition.define_string_parameter("param1")
        definition.define_string_parameter("param1")


def test_parameter_order():
    definition = AdapterDefinition("key")
    definition.define_string_parameter("param1")
    definition.define_string_parameter("param2")
    identifiers = definition.to_json()["adapter_instance"]["identifiers"]
    param1 = list(filter(lambda i: i["key"] == "param1", identifiers))[0]
    param2 = list(filter(lambda i: i["key"] == "param2", identifiers))[0]
    assert param1["display_order"] < param2["display_order"]


def test_enum_default_included():
    definition = AdapterDefinition("key")
    definition.define_enum_parameter("param1", values=["Item1", "Item2"], default="Item1")
    identifiers = definition.to_json()["adapter_instance"]["identifiers"]
    param1 = list(filter(lambda i: i["key"] == "param1", identifiers))[0]
    assert len(param1["enum_values"]) == 2


def test_enum_default_not_included():
    definition = AdapterDefinition("key")
    definition.define_enum_parameter("param1", values=["Item1", "Item2"], default="Item3")
    identifiers = definition.to_json()["adapter_instance"]["identifiers"]
    param1 = list(filter(lambda i: i["key"] == "param1", identifiers))[0]
    assert len(param1["enum_values"]) == 3


def test_duplicate_credential_type_keys_not_allowed():
    definition = AdapterDefinition("key")
    definition.define_credential_type("ldap")
    with pytest.raises(DuplicateKeyException) as dke:
        definition.define_credential_type("ldap")


def test_credential_parameter_order():
    definition = AdapterDefinition("key")
    credential = definition.define_credential_type()
    credential.define_string_parameter("username")
    credential.define_string_parameter("password")
    fields = definition.to_json()["credential_types"][0]["fields"]
    param1 = list(filter(lambda i: i["key"] == "username", fields))[0]
    param2 = list(filter(lambda i: i["key"] == "password", fields))[0]
    assert param1["display_order"] < param2["display_order"]


def test_duplicate_credential_parameter_keys_not_allowed():
    definition = AdapterDefinition("adapter")
    credential = definition.define_credential_type("ldap")
    credential.define_int_parameter("key")
    with pytest.raises(DuplicateKeyException) as dke:
        credential.define_string_parameter("key")


def test_credential_enum_default_included():
    definition = AdapterDefinition("key")
    credential = definition.define_credential_type()
    credential.define_enum_parameter("param1", values=["Item1", "Item2"], default="Item1")
    fields = definition.to_json()["credential_types"][0]["fields"]
    param1 = list(filter(lambda i: i["key"] == "param1", fields))[0]
    assert len(param1["enum_values"]) == 2


def test_credential_enum_default_not_included():
    definition = AdapterDefinition("key")
    credential = definition.define_credential_type()
    credential.define_enum_parameter("param1", values=["Item1", "Item2"], default="Item3")
    fields = definition.to_json()["credential_types"][0]["fields"]
    param1 = list(filter(lambda i: i["key"] == "param1", fields))[0]
    assert len(param1["enum_values"]) == 3


def test_duplicate_object_type_keys_not_allowed():
    definition = AdapterDefinition("key")
    definition.define_object_type("obj")
    with pytest.raises(DuplicateKeyException) as dke:
        definition.define_object_type("obj")


def test_adapter_definition_example():
    definition = AdapterDefinition("adapter_key", "Adapter Label")

    definition.define_string_parameter("Host", description="Hostname of the target.")
    definition.define_int_parameter("Port", required=False, description="Port to connect to on the target.", default=443)
    definition.define_enum_parameter("API Version", advanced=True, values=["1.1", "1.2", "2+"], default="2+", description="Select the API version the target supports.")

    credential = definition.define_credential_type()
    credential.define_string_parameter("Username", label="User Name")
    credential.define_password_parameter("Password")
    credential.define_enum_parameter("Authentication Source", values=["Local", "LDAP"], default="Local")


def test_adapter_definition_example_multiple_credential_types():
    definition = AdapterDefinition("adapter_key", "Adapter Label")
    definition.define_string_parameter("Host", description="Hostname of the target.")
    definition.define_int_parameter("Port", description="Port to connect to on the target.", default=443)
    definition.define_enum_parameter("API Version", values=["1.1", "1.2", "2+"], default="2+", description="Select the API version the target supports.")

    local_credential = definition.define_credential_type("Local")
    local_credential.define_string_parameter("Username")
    local_credential.define_password_parameter("Password")

    ldap_credential = definition.define_credential_type("LDAP")
    ldap_credential.define_string_parameter("Domain")
    ldap_credential.define_string_parameter("Username")
    ldap_credential.define_password_parameter("Password")
