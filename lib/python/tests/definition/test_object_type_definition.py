#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import pytest

from vrops.definition.exceptions import KeyException
from vrops.definition.object_type import ObjectType


def test_object_type_definition_default_label():
    key = "key"
    definition = ObjectType(key)
    assert definition.label == key


def test_missing_adapter_key_raises_exception():
    with pytest.raises(KeyException):
        definition = ObjectType(key=None)
