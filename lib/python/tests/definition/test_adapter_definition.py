#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import pytest
from aria.ops.definition.adapter_definition import AdapterDefinition
from aria.ops.definition.credential_type import CredentialPasswordParameter
from aria.ops.definition.credential_type import CredentialStringParameter
from aria.ops.definition.credential_type import CredentialType
from aria.ops.definition.exceptions import DuplicateKeyException
from aria.ops.definition.exceptions import KeyException
from aria.ops.definition.object_type import ObjectType


def test_adapter_definition_default_label() -> None:
    key = "key"
    definition = AdapterDefinition(key)
    assert definition.label == key


def test_missing_adapter_key_raises_exception() -> None:
    with pytest.raises(KeyException):
        AdapterDefinition(key=None)


def test_invalid_type_adapter_key_raises_exception() -> None:
    with pytest.raises(KeyException):
        AdapterDefinition(key=5)


def test_empty_adapter_key_raises_exception() -> None:
    with pytest.raises(KeyException):
        AdapterDefinition(key="")


def test_blank_adapter_key_raises_exception() -> None:
    with pytest.raises(KeyException):
        AdapterDefinition(key="\n ")


def test_leading_digit_adapter_key_raises_exception() -> None:
    with pytest.raises(KeyException):
        AdapterDefinition(key="6key")


def test_key_with_special_character_raises_exception() -> None:
    with pytest.raises(KeyException):
        AdapterDefinition("te$t")


def test_containing_whitespace_adapter_key_raises_exception() -> None:
    with pytest.raises(KeyException) as ke:
        AdapterDefinition(key="ke\ty")
    assert str(ke.value) == "Adapter key cannot contain whitespace."


def test_complex_valid_adapter_key() -> None:
    try:
        AdapterDefinition(key="This_15_a_valid_KEY")
    except KeyException as e:
        assert e is False


def test_adapter_definition_label() -> None:
    key = "key"
    label = "Label"
    definition = AdapterDefinition(key, label)
    assert definition.label == label


def test_adapter_definition_default_ai_key() -> None:
    key = "key"
    definition = AdapterDefinition(key)
    assert definition.adapter_instance_key == f"{key}_adapter_instance"


def test_adapter_definition_default_ai_label() -> None:
    key = "key"
    definition = AdapterDefinition(key)
    assert definition.adapter_instance_label == f"{definition.label} Adapter Instance"


def test_adapter_definition_default_ai_label_2() -> None:
    key = "key"
    label = "Label"
    definition = AdapterDefinition(key, label)
    assert definition.adapter_instance_label == f"{definition.label} Adapter Instance"


def test_duplicate_parameter_keys_not_allowed() -> None:
    with pytest.raises(DuplicateKeyException) as dke:
        definition = AdapterDefinition("key")
        definition.define_string_parameter("param1")
        definition.define_string_parameter("param1")


def test_parameter_order() -> None:
    definition = AdapterDefinition("key")
    definition.define_string_parameter("param1")
    definition.define_string_parameter("param2")
    identifiers = definition.to_json()["adapter_instance"]["identifiers"]
    param1 = list(filter(lambda i: i["key"] == "param1", identifiers))[0]
    param2 = list(filter(lambda i: i["key"] == "param2", identifiers))[0]
    assert param1["display_order"] < param2["display_order"]


def test_enum_default_included() -> None:
    definition = AdapterDefinition("key")
    definition.define_enum_parameter(
        "param1", values=["Item1", "Item2"], default="Item1"
    )
    identifiers = definition.to_json()["adapter_instance"]["identifiers"]
    param1 = list(filter(lambda i: i["key"] == "param1", identifiers))[0]
    assert len(param1["enum_values"]) == 2


def test_enum_default_not_included() -> None:
    definition = AdapterDefinition("key")
    definition.define_enum_parameter(
        "param1", values=["Item1", "Item2"], default="Item3"
    )
    identifiers = definition.to_json()["adapter_instance"]["identifiers"]
    param1 = list(filter(lambda i: i["key"] == "param1", identifiers))[0]
    assert len(param1["enum_values"]) == 3


def test_duplicate_credential_type_keys_not_allowed() -> None:
    definition = AdapterDefinition("key")
    definition.define_credential_type("ldap")
    with pytest.raises(DuplicateKeyException) as dke:
        definition.define_credential_type("ldap")


def test_credential_parameter_order() -> None:
    definition = AdapterDefinition("key")
    credential = definition.define_credential_type()
    credential.define_string_parameter("username")
    credential.define_string_parameter("password")
    credential.define_int_parameter("token")
    fields = definition.to_json()["credential_types"][0]["fields"]
    param1 = list(filter(lambda i: i["key"] == "username", fields))[0]
    param2 = list(filter(lambda i: i["key"] == "password", fields))[0]
    param3 = list(filter(lambda i: i["key"] == "token", fields))[0]
    assert param1["display_order"] < param2["display_order"]
    assert param2["display_order"] < param3["display_order"]


def test_duplicate_credential_parameter_keys_not_allowed() -> None:
    definition = AdapterDefinition("adapter")
    credential = definition.define_credential_type("ldap")
    credential.define_int_parameter("key")
    with pytest.raises(DuplicateKeyException) as dke:
        credential.define_string_parameter("key")


def test_credential_enum_default_included() -> None:
    definition = AdapterDefinition("key")
    credential = definition.define_credential_type()
    credential.define_enum_parameter(
        "param1", values=["Item1", "Item2"], default="Item1"
    )
    fields = definition.to_json()["credential_types"][0]["fields"]
    param1 = list(filter(lambda i: i["key"] == "param1", fields))[0]
    assert len(param1["enum_values"]) == 2


def test_credential_enum_default_not_included() -> None:
    definition = AdapterDefinition("key")
    credential = definition.define_credential_type()
    credential.define_enum_parameter(
        "param1", values=["Item1", "Item2"], default="Item3"
    )
    fields = definition.to_json()["credential_types"][0]["fields"]
    param1 = list(filter(lambda i: i["key"] == "param1", fields))[0]
    assert len(param1["enum_values"]) == 3


def test_duplicate_object_type_keys_not_allowed() -> None:
    definition = AdapterDefinition("key")
    definition.define_object_type("obj")
    with pytest.raises(DuplicateKeyException) as dke:
        definition.define_object_type("obj")


def test_add_credential_parameters() -> None:
    definition = AdapterDefinition("key")
    credential = definition.define_credential_type("cred")
    param1 = CredentialStringParameter("username")
    param2 = CredentialPasswordParameter("password")
    credential.add_parameters([param1, param2])
    assert len(credential.credential_parameters) == 2


def test_add_credential_types() -> None:
    definition = AdapterDefinition("key")
    type1 = CredentialType("Type1")
    type2 = CredentialType("Type2")
    definition.add_credential_types([type1, type2])
    assert len(definition.credentials) == 2


def test_add_object_types() -> None:
    definition = AdapterDefinition("key")
    type1 = ObjectType("Type1")
    type2 = ObjectType("Type2")
    definition.add_object_types([type1, type2])
    assert len(definition.object_types) == 2


def test_adapter_definition_example() -> None:
    definition = AdapterDefinition("adapter_key", "Adapter Label")

    definition.define_string_parameter("Host", description="Hostname of the target.")
    definition.define_int_parameter(
        "Port",
        required=False,
        description="Port to connect to on the target.",
        default=443,
    )
    definition.define_enum_parameter(
        "API Version",
        advanced=True,
        values=["1.1", "1.2", "2+"],
        default="2+",
        description="Select the API version the target supports.",
    )

    credential = definition.define_credential_type()
    credential.define_string_parameter("Username", label="User Name")
    credential.define_password_parameter("Password")
    credential.define_enum_parameter(
        "Authentication Source", values=["Local", "LDAP"], default="Local"
    )


def test_adapter_definition_example_multiple_credential_types() -> None:
    definition = AdapterDefinition("adapter_key", "Adapter Label")
    definition.define_string_parameter("Host", description="Hostname of the target.")
    definition.define_int_parameter(
        "Port", description="Port to connect to on the target.", default=443
    )
    definition.define_enum_parameter(
        "API Version",
        values=["1.1", "1.2", "2+"],
        default="2+",
        description="Select the API version the target supports.",
    )

    local_credential = definition.define_credential_type("Local")
    local_credential.define_string_parameter("Username")
    local_credential.define_password_parameter("Password")

    ldap_credential = definition.define_credential_type("LDAP")
    ldap_credential.define_string_parameter("Domain")
    ldap_credential.define_string_parameter("Username")
    ldap_credential.define_password_parameter("Password")
