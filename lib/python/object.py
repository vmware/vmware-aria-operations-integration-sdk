from __future__ import annotations

__author__ = 'VMware, Inc.'
__copyright__ = 'Copyright 2022 VMware, Inc. All rights reserved.'

from attribute import Metric, Property
from event import Event


class Key:
    """Object's Key class, used for identifying objects

    Objects are identified by the adapter kind, object kind, and one or more identifiers.

    Identifiers can be either the object's 'name', or one or more 'Identifier' key-value pairs.
    In order for an 'Identifier' to be used for identification, it must have 'is_part_of_uniqueness' set to True
    (this is the default).

    Two objects with the same Key are not permitted to be returned.

    Objects must be created with the full key. Keys should not change after the object has been created.

    All objects with the same adapter kind and object kind must have the same set of identifier keys that have
    'is_part_of_uniqueness' set to True.
    """
    def __init__(self, adapter_kind: str, object_kind: str, name: str, identifiers=None):
        self.adapter_kind = adapter_kind
        self.object_kind = object_kind
        self.name = name
        if identifiers is None:
            identifiers = []
        self.identifiers = {identifier.key: identifier for identifier in identifiers}

    def __repr__(self):
        return f"{self.adapter_kind}:{self.object_kind}:{self.identifiers}"

    def __key(self):
        if sum(map(lambda ident: ident.is_part_of_uniqueness, self.identifiers)) == 0:
            # If there are no identifiers, or if all identifiers are not part of uniqueness, the name is used as
            # uniquely identifying
            return self.adapter_kind, self.object_kind, self.name
        else:
            # Otherwise, if there is at least one identifier that is part of uniqueness, name is not used for
            # identification
            return self.adapter_kind, self.object_kind, self.identifiers

    def __eq__(self, other):
        if isinstance(other, Key):
            # TODO: raise exception if the object types are the same but identifier keys don't match?
            return self.__key() == other.__key()
        else:
            return False

    def __hash__(self):
        return hash(self.__key())

    def get_json(self):
        return {
            "name": self.name,
            "adapterKind": self._key.adapter_kind,
            "objectKind": self._key.object_kind,
            "identifiers": [identifier.get_json() for (key, identifier) in self._key.identifiers.items()],
        }


class IdentifierUniquenessException(Exception):
    pass


class Identifier:
    def __init__(self, key: str, value: str, is_part_of_uniqueness: bool = True):
        self.key = key
        self.value = value
        self.is_part_of_uniqueness = is_part_of_uniqueness

    def __repr__(self):
        u = "*" if self.is_part_of_uniqueness else ""
        return f"{self.key}{u}:{self.value}"

    def __key(self):
        if self.is_part_of_uniqueness:
            # 'True' is included as the second tuple because otherwise we could get a collision between a key that has
            # a value of 'False' and a key that is not a part of uniqueness
            return self.key, True, self.value
        return self.key, False

    def __eq__(self, other):
        if isinstance(other, Identifier):
            if self.key == other.key and self.is_part_of_uniqueness != other.is_part_of_uniqueness:
                # TODO: is there a better way we can handle this case?
                raise IdentifierUniquenessException(f"Identifier '{self.key}' has an inconsistent uniqueness attribute")
            return self.__key() == other.__key()
        return False

    def __hash__(self):
        return hash(self.__key())

    def get_json(self):
        return {
            "key": self.key,
            "value": self.value,
            "isPartOfUniqueness": self.is_part_of_uniqueness
        }


class Object:
    """Represents an object (resource) in vROps.

    Contains metrics, properties, events, and relationships to other objects. Each object is identified by a unique
    key.
    """

    def __init__(self, key: Key):
        self._key = key
        self.metrics = []
        self.properties = []
        self.events = []
        self.parents = set()
        self.children = set()

    def add_metric(self, metric: Metric):
        self.metrics.append(metric)

    def with_metric(self, *args, **kwargs):
        self.metrics.append(Metric(*args, **kwargs))
        return self

    def add_property(self, property_: Property):
        self.properties.append(property_)

    def with_property(self, *args, **kwargs):
        self.properties.append(Metric(*args, **kwargs))
        return self

    def add_event(self, event: Event):
        self.events.append(event)

    def with_event(self, *args, **kwargs):
        self.events.append(Event(*args, **kwargs))
        return self

    def add_parent(self, parent: Object):
        self.parents.add(parent._key)
        parent.children.add(self._key)

    def add_child(self, child: Object):
        self.children.add(child._key)
        child.parents.add(self._key)

    def get_json(self):
        return {
            "key": self._key.get_json(),
            "metrics": [metric.get_json() for metric in self.metrics],
            "properties": [prop.get_json() for prop in self.properties],
            "events": [event.get_json() for event in self.events]
        }
