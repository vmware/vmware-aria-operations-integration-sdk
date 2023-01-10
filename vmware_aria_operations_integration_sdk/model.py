#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple


@dataclass(frozen=True)
class ObjectType:
    adapterKind: str
    objectKind: str

    def __repr__(self) -> str:
        return f"{self.adapterKind}::{self.objectKind}"


def _get_type(json: Dict) -> Optional[ObjectType]:
    if not json:
        return None
    if "adapterKind" not in json:
        object_key = json.get("key", {})
    else:
        object_key = json
    adapter_type = object_key.get("adapterKind")
    object_type = object_key.get("objectKind")
    if adapter_type and object_type:
        return ObjectType(adapter_type, object_type)
    return None


@dataclass(frozen=True)
class Identifier:
    key: str
    value: str

    def __repr__(self) -> str:
        return f"{self.key}: {self.value}"


def _get_identifier(json: Dict) -> Optional[Identifier]:
    if not json:
        return None
    if json.get("isPartOfUniqueness"):
        key = json.get("key")
        value = json.get("value", "")
        if key:
            return Identifier(key, value)
    return None


def _get_identifiers(json: Dict) -> Tuple[Identifier, ...]:
    if not json:
        return tuple()
    identifiers = json.get("identifiers", [])
    identifiers = [_get_identifier(identifier) for identifier in identifiers]
    return tuple(
        sorted([id for id in identifiers if id is not None], key=lambda id: id.key)
    )


@dataclass(frozen=True)
class ObjectId:
    name: str
    objectKind: ObjectType
    identifiers: Tuple[Identifier, ...]

    def __str__(self) -> str:
        return f"{self.name} ({self.objectKind})"

    def __repr__(self) -> str:
        ids = " :: ".join(map(str, self.identifiers))
        return f"{self.name} ({self.objectKind} - {ids})"


def _get_object_id(json: Optional[Dict]) -> Optional[ObjectId]:
    if not json:
        return None
    name = json.get("name")
    object_type = _get_type(json)
    identifiers = _get_identifiers(json)
    if name and object_type:
        return ObjectId(name, object_type, identifiers)
    return None
