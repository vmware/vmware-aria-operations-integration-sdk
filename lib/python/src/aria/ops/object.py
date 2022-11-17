from __future__ import annotations

#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import copy
from typing import Optional

from aria.ops.data import Metric, Property
from aria.ops.event import Event


class Key:
    """ Object's Key class, used for identifying Objects

    Objects are identified by the Adapter Kind, Object Kind, and one or more Identifiers.

    Identifiers can be either the Object's 'name', or one or more 'Identifier' key-value pairs.
    In order for an 'Identifier' to be used for identification, it must have 'is_part_of_uniqueness' set to True
    (this is the default).

    Two Objects with the same Key are not permitted in a :class:`Result`.

    Objects must be created with the full key. Keys should not change after the Object has been created.

    All Objects with the same Adapter Kind and Object Kind must have the same set of Identifiers that have
    'is_part_of_uniqueness' set to True.
    """

    def __init__(self, adapter_kind: str, object_kind: str, name: str, identifiers: list[Identifier] = None) -> None:
        """ Initializes a Key, which uniquely identifies a vROps Object

        :param adapter_kind: The Adapter Kind this Object is associated with.
        :param object_kind: The Object Kind (e.g., class) of this Object.
        :param name: A human-readable name for this Object. Should be unique if possible.
        :param identifiers: A list of :class:`Identifier` that uniquely identify the Object. If none are present than
            the name must be unique and is used for identification. All Objects with the same adapter kind and Object
            kind must have the same set of identifiers.
        """
        self.adapter_kind = adapter_kind
        self.object_kind = object_kind
        self.name = name
        if identifiers is None:
            identifiers = []
        self.identifiers = {identifier.key: identifier for identifier in identifiers}

    def __repr__(self) -> str:
        return f"{self.adapter_kind}:{self.object_kind}:{self.identifiers}"

    def __key(self) -> tuple:
        # Sort all identifiers by 'key' that are part of uniqueness
        unique_identifiers = sorted(
            filter(lambda id_: id_.is_part_of_uniqueness, self.identifiers.values()),
            key=lambda id_: id_.key
        )
        if len(unique_identifiers) == 0:
            # If there are no identifiers, or if all identifiers are not part of uniqueness, the name is used as
            # uniquely identifying
            return self.adapter_kind, self.object_kind, self.name
        else:
            # Otherwise, if there is at least one identifier that is part of uniqueness, name is not used for
            # identification. Add each of the unique identifiers to the tuple, sorted by key
            return (self.adapter_kind, self.object_kind) + tuple(unique_identifiers)

    def __eq__(self, other) -> bool:
        if isinstance(other, Key):
            # TODO: raise exception if the object types are the same but identifier keys don't match?
            return self.__key() == other.__key()
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.__key())

    def get_identifier(self, key):
        """ Return the value for the given identifier key

        :param key: The identifier key
        :return: The value associated with the identifier, or 'None' if the identifier key does not exist
        """
        if self.identifiers.get(key):
            return self.identifiers[key].value
        return None

    def get_json(self) -> dict:
        """ Get a JSON representation of this Key

        Returns a JSON representation of this Key in the format required by vROps.

        :return: A JSON representation of this Key
        """
        return {
            "name": self.name,
            "adapterKind": self.adapter_kind,
            "objectKind": self.object_kind,
            "identifiers": [identifier.get_json() for identifier in self.identifiers.values()],
        }


class IdentifierUniquenessException(Exception):
    """ Exception when two Objects of the same type have the same identifier but the `is_part_of_uniqueness` attribute
    does not match.
    """
    pass


class Identifier:
    """ Represents a piece of data that identifies an Object.
    """

    def __init__(self, key: str, value: str, is_part_of_uniqueness: bool = True) -> None:
        """ Creates an identifier which is used as part of an Object's identification in a :class:`Key`

        Represents a piece of data that identifies an Object. If `is_part_of_uniqueness` is False, this data can
        change over time without creating a new Object. This is primarily used for human-readable values that are useful
        in identification purposes, but may change at times.

        :param key: A key that determines which identifier the value corresponds to.
        :param value: The value of the identifier.
        :param is_part_of_uniqueness: Determines if this key/value pair is used in the identification process
        """
        self.key = key
        self.value = value
        self.is_part_of_uniqueness = is_part_of_uniqueness

    def __repr__(self) -> str:
        u = "*" if self.is_part_of_uniqueness else ""
        return f"{self.key}{u}:{self.value}"

    def __key(self) -> tuple:
        if self.is_part_of_uniqueness:
            # 'True' is included as the second tuple because otherwise we could get a collision between a key that has
            # a value of 'False' and a key that is not a part of uniqueness
            return self.key, True, self.value
        return self.key, False

    def __eq__(self, other) -> bool:
        if isinstance(other, Identifier):
            if self.key == other.key and self.is_part_of_uniqueness != other.is_part_of_uniqueness:
                # TODO: is there a better way we can handle this case?
                raise IdentifierUniquenessException(f"Identifier '{self.key}' has an inconsistent uniqueness attribute")
            return self.__key() == other.__key()
        return False

    def __hash__(self) -> int:
        return hash(self.__key())

    def get_json(self) -> dict:
        """Get a JSON representation of this Identifier

        Returns a JSON representation of this Identifier in the format required by vROps.

        :return: A JSON representation of this Identifier
        """
        return {
            "key": self.key,
            "value": self.value,
            "isPartOfUniqueness": self.is_part_of_uniqueness
        }


class Object:
    """Represents an Object (resource) in vROps.

    Contains :class:`Metric`, :class:`Property`, :class:`Event`, and relationships to other Objects. Each Object is
    identified by a unique :class:`Key`.
    """

    def __init__(self, key: Key) -> None:
        """ Create a new Object with a given Key.

        The preferred way to create a new Object is to call the :class:`Result.object` method on the :class:`Result`
        class, which ensures that for a given key only one Object exists.

        :param key: The :class:`Key` that uniquely identifies this Object
        """
        self._key = key
        self._metrics = []
        self._properties = []
        self._events = set()
        self._parents = set()
        self._children = set()

    def get_key(self):
        """ Get a copy of the Object's Key.

        An object's Key cannot change after it has been created.

        :return: A copy of the object's key
        """
        return copy.deepcopy(self._key)

    def get_identifier_value(self, identifier_key):
        """ Retrieve the value of a given identifier

        :param identifier_key: Key of the identifier
        :return: value associated with the identifier, or None if identifier does not exist
        """
        return self._key.get_identifier(identifier_key)

    def add_metric(self, metric: Metric) -> None:
        """ Method that adds a single Metric data point to this Object

        :param metric: A :class:`Metric` data point to add to this Object
        :return: None
        """
        self._metrics.append(metric)

    def add_metrics(self, metrics: list[Metric]) -> None:
        """ Method that adds a list of Metric data points to this Object

        :param metrics: A list of :class:`Metric` data points to add to this Object
        :return: None
        """
        for metric in metrics:
            self.add_metric(metric)

    def with_metric(self, *args, **kwargs) -> None:
        """ Method that handles creating a :class:`Metric` data point, and adding to this Object.

        The signature matches :class:`Metric.__init__`.
        :return: None
        """
        self.add_metric(Metric(*args, **kwargs))

    def get_metric(self, key) -> list[Metric]:
        """

        :param key: Metric key of the metric to return.
        :return: All metrics matching the given key.
        """
        return list(filter(lambda metric: metric.key == key, self._metrics))

    def add_property(self, property_: Property) -> None:
        """ Method that adds a single Property value to this Object

        :param property_: A :class:`Property` value to add to this Object
        :return: None
        """
        self._properties.append(property_)

    def add_properties(self, properties: list[Property]) -> None:
        """ Method that adds a list of Property values to this Object

        :param properties: A list of :class:`Property` values to add to this Object
        :return: None
        """
        for property_ in properties:
            self.add_property(property_)

    def with_property(self, *args, **kwargs) -> None:
        """ Method that handles creating a :class:`Property` value, and adding to this Object.

        The signature matches :class:`Property.__init__`.
        :return: None
        """
        self.add_property(Property(*args, **kwargs))

    def get_property(self, key) -> list[Property]:
        """

        :param key: Property key of the property to return.
        :return: All properties matching the given key
        """
        return list(filter(lambda property_: property_.key == key, self._properties))

    def get_property_values(self, key) -> list[str]:
        """

        :param key: Property key of the property to return.
        :return:  return a list the property values based on chronological order
        """
        # find matching properties
        properties = self.get_property(key)

        # sort properties by timestamp from oldest  to newest
        properties.sort(key=lambda property: property.timestamp)

        return [p.value for p in properties]

    def get_last_property_value(self, key) -> str | None:
        """

        :param key: Property key of the property to return.
        :return:  return the last value of the property with the matching key or None
        if the property Key doesn't match any property
        """
        properties = self.get_property_values(key)

        if not properties:
            return None
        else:
            return properties[-1]

    def add_event(self, event: Event) -> None:
        """ Method that adds a single Event to this Object

        :param event: An :class:`Event` to add to this Object
        :return: None
        """
        self._events.add(event)

    def add_events(self, events: list[Event]) -> None:
        """ Method that adds a list of Events to this Object

        :param events: A list of :class:`Event` to add to this Object
        :return: None
        """
        for event in events:
            self.add_event(event)

    def with_event(self, *args, **kwargs) -> None:
        """ Method that handles creating an :class:`Event`, and adding to this Object.

        The signature matches :class:`Event.__init__`.
        :return: None
        """
        self.add_event(Event(*args, **kwargs))

    def add_parent(self, parent: Object) -> None:
        """ Method that adds a parent Object to this Object.

        This Object will also be added as a child to the parent.

        Relationship cycles are not permitted.

        :param parent: Parent :class:`Object`
        :return: None
        """
        self._parents.add(parent._key)
        parent._children.add(self._key)

    def add_parents(self, parents: list[Object]) -> None:
        """ Method that adds a list of parent Objects to this Object.

        This Object will also be added as a child to each of the parents.

        Relationship cycles are not permitted.

        :param parents: A list of parent :class:`Object`
        :return: None
        """
        for parent in parents:
            self.add_parent(parent)

    def get_parents(self) -> set[Object]:
        """
        :return: A set of all objects that are parents of this object
        """
        return self._parents

    def add_child(self, child: Object) -> None:
        """ Method that adds a child Object to this Object.

        This Object will also be added as a parent to the child.

        Relationship cycles are not permitted.

        :param child: Child :class:`Object`
        :return: None
        """
        self._children.add(child._key)
        child._parents.add(self._key)

    def add_children(self, children: list[Object]) -> None:
        """ Method that adds a list of child Objects to this Object.

        This Object will also be added as a parent to each of the children.

        Relationship cycles are not permitted.

        :param children: A list of child :class:`Object`
        :return: None
        """
        for child in children:
            self.add_child(child)

    def get_children(self) -> set[Object]:
        """
        :return: A set of all objects that are children of this object
        """
        return self._children

    def get_json(self) -> dict:
        """Get a JSON representation of this Object

        Returns a JSON representation of this Object in the format required by vROps.

        :return: A JSON representation of this Object
        """
        return {
            "key": self._key.get_json(),
            "metrics": [metric.get_json() for metric in self._metrics],
            "properties": [prop.get_json() for prop in self._properties],
            "events": [event.get_json() for event in self._events]
        }
