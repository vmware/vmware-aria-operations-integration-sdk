from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ObjectType:
    adapterKind: str
    objectKind: str

    def __repr__(self):
        return f"{self.adapterKind}::{self.objectKind}"


def _get_type(json) -> Optional[ObjectType]:
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

    def __repr__(self):
        return f"{self.key}: {self.value}"


def _get_identifier(json) -> Optional[Identifier]:
    if not json:
        return None
    if json.get("isPartOfUniqueness"):
        key = json.get("key")
        value = json.get("value")
        return Identifier(key, value)
    return None


def _get_identifiers(json) -> tuple[Identifier]:
    if not json:
        return tuple()
    identifiers = json.get("identifiers", [])
    identifiers = [_get_identifier(identifier) for identifier in identifiers]
    identifiers = tuple(sorted([id for id in identifiers if id is not None], key=lambda id: id.key))
    return identifiers


@dataclass(frozen=True)
class ObjectId:
    name: str
    objectKind: ObjectType
    identifiers: [Identifier]

    def __str__(self):
        return f"{self.name} ({self.objectKind})"

    def __repr__(self):
        ids = " :: ".join(map(str, self.identifiers))
        return f"{self.name} ({self.objectKind} - {ids})"


def _get_object_id(json) -> Optional[ObjectId]:
    if not json:
        return None
    name = json.get("name")
    object_type = _get_type(json)
    identifiers = _get_identifiers(json)
    return ObjectId(name, object_type, identifiers)
