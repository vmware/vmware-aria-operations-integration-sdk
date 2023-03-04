#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from aria.ops.object import Identifier
from aria.ops.object import Key


def test_get_identifier() -> None:
    identifier1 = Identifier("key1", "value1")
    identifier2 = Identifier("key2", "value2")
    key = Key("adapter_kind", "object_kind", "name", [identifier1, identifier2])
    assert key.get_identifier("key1") == "value1"


def test_get_identifier_with_default() -> None:
    identifier1 = Identifier("key1", "value1")
    identifier2 = Identifier("key2", "value2")
    key = Key("adapter_kind", "object_kind", "name", [identifier1, identifier2])
    assert key.get_identifier("key2", "default") == "value2"


def test_get_not_existing_identifier() -> None:
    identifier1 = Identifier("key1", "value1")
    identifier2 = Identifier("key2", "value2")
    key = Key("adapter_kind", "object_kind", "name", [identifier1, identifier2])
    assert key.get_identifier("bad_key") is None


def test_get_not_existing_identifier_with_default() -> None:
    identifier1 = Identifier("key1", "value1")
    identifier2 = Identifier("key2", "value2")
    key = Key("adapter_kind", "object_kind", "name", [identifier1, identifier2])
    assert key.get_identifier("bad_key", "default") == "default"


def test_get_empty_identifier() -> None:
    identifier1 = Identifier("key1", "")
    identifier2 = Identifier("key2", "value2")
    key = Key("adapter_kind", "object_kind", "name", [identifier1, identifier2])
    assert key.get_identifier("key1") == ""


def test_get_empty_identifier_with_default() -> None:
    identifier1 = Identifier("key1", "")
    identifier2 = Identifier("key2", "value2")
    key = Key("adapter_kind", "object_kind", "name", [identifier1, identifier2])
    assert key.get_identifier("key1", "default") == "default"
