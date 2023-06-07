from __future__ import annotations

import copy
from typing import Any
from typing import List
from typing import Optional
from typing import Set

from aria.ops.data import Metric
from aria.ops.data import Property
from aria.ops.event import Event


#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0


class Key:
    """Object's Key class, used for identifying Objects

    Objects are identified by the Adapter Kind, Object Kind, and one or more Identifiers.

    Identifiers can be either the Object's 'name', or one or more 'Identifier' key-value pairs.
    In order for an 'Identifier' to be used for identification, it must have 'is_part_of_uniqueness' set to True
    (this is the default).

    Two Objects with the same Key are not permitted in a :class:`Result`.

    Objects must be created with the full key. Keys should not change after the Object has been created.

    All Objects with the same Adapter Kind and Object Kind must have the same set of Identifiers that have
    'is_part_of_uniqueness' set to True.
    """

    def __init__(
        self,
        adapter_kind: str,
        object_kind: str,
        name: str,
        identifiers: Optional[List[Identifier]] = None,
    ) -> None:
        """Initializes a Key, which uniquely identifies a vROps Object.

        Args:
            adapter_kind: The Adapter Kind this Object is associated with.
            object_kind: The Object Kind (e.g., class) of this Object.
            name: A human-readable name for this Object. Should be unique if possible.
            identifiers: A list of :class:`Identifier` that uniquely identify the Object. If none are present than
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
            key=lambda id_: id_.key,
        )
        if len(unique_identifiers) == 0:
            # If there are no identifiers, or if all identifiers are not part of uniqueness, the name is used as
            # uniquely identifying
            return self.adapter_kind, self.object_kind, self.name
        else:
            # Otherwise, if there is at least one identifier that is part of uniqueness, name is not used for
            # identification. Add each of the unique identifiers to the tuple, sorted by key
            return (self.adapter_kind, self.object_kind) + tuple(unique_identifiers)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Key):
            # TODO: raise exception if the object types are the same but identifier keys don't match?
            return self.__key() == other.__key()
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.__key())

    def get_identifier(
        self, key: str, default_value: Optional[str] = None
    ) -> Optional[str]:
        """Return the value for the given identifier key.

        Args:
            key: The identifier key.
            default_value: An optional default value.

        Returns:
            The value associated with the identifier.
            If the value associated with the identifier is empty and 'default_value' is
            provided, returns 'default_value'.
            If the identifier does not exist, returns default_value if provided, else 'None'.
        """
        if self.identifiers.get(key):
            if self.identifiers[key].value or default_value is None:
                return self.identifiers[key].value
            return default_value
        return default_value

    def get_json(self) -> dict:
        """Get a JSON representation of this Key.

        This method returns a JSON representation of this Key in the format required by vROps.

        Returns:
            dict: A JSON representation of this Key.
        """
        return {
            "name": self.name,
            "adapterKind": self.adapter_kind,
            "objectKind": self.object_kind,
            "identifiers": [
                identifier.get_json() for identifier in self.identifiers.values()
            ],
        }


class IdentifierUniquenessException(Exception):
    """Exception when two Objects of the same type have the same identifier but the `is_part_of_uniqueness` attribute
    does not match.
    """

    pass


class Identifier:
    """Represents a piece of data that identifies an Object."""

    def __init__(
        self, key: str, value: str, is_part_of_uniqueness: bool = True
    ) -> None:
        """Creates an identifier which is used as part of an Object's identification in a :class:`Key`.

        This class represents a piece of data that identifies an Object. If `is_part_of_uniqueness` is False, this data
        can change over time without creating a new Object. This is primarily used for human-readable values that are
        useful in identification purposes, but may change at times.

        Args:
            key: A key that determines which identifier the value corresponds to.
            value: The value of the identifier.
            is_part_of_uniqueness: Determines if this key/value pair is used in the identification process.
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

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Identifier):
            if (
                self.key == other.key
                and self.is_part_of_uniqueness != other.is_part_of_uniqueness
            ):
                # TODO: is there a better way we can handle this case?
                raise IdentifierUniquenessException(
                    f"Identifier '{self.key}' has an inconsistent uniqueness attribute"
                )
            return self.__key() == other.__key()
        return False

    def __hash__(self) -> int:
        return hash(self.__key())

    def get_json(self) -> dict:
        """Get a JSON representation of this Identifier.

        This method returns a JSON representation of this Identifier in the format required by vROps.

        Returns:
            dict: A JSON representation of this Identifier.
        """
        return {
            "key": self.key,
            "value": self.value,
            "isPartOfUniqueness": self.is_part_of_uniqueness,
        }


class Object:
    """Represents an Object (resource) in vROps.

    Contains :class:`Metric`, :class:`Property`, :class:`Event`, and relationships to other Objects. Each Object is
    identified by a unique :class:`Key`.
    """

    def __init__(self, key: Key) -> None:
        """Create a new Object with a given Key.

        This method is the preferred way to create a new Object. It should be called from the :class:`Result.object`
        method on the :class:`Result` class, which ensures that for a given key only one Object exists.

        Args:
            key: The :class:`Key` that uniquely identifies this Object.
        """

        self._key: Key = key
        self._metrics: List[Metric] = []
        self._properties: List[Property] = []
        self._events: Set[Event] = set()
        self._parents: Set[Key] = set()
        self._children: Set[Key] = set()
        self._updated_children: bool = False

    def get_key(self) -> Key:
        """Get a copy of the Object's Key.

        An object's Key cannot change after it has been created.

        Returns:
            A copy of the object's key.
        """
        return copy.deepcopy(self._key)

    def adapter_type(self) -> str:
        """Get the adapter type of this object

        Returns:
             The adapter type of this object
        """
        return self._key.adapter_kind

    def object_type(self) -> str:
        """Get the type of this object

        Returns:
             The type of this object
        """
        return self._key.object_kind

    def get_identifier_value(
        self, identifier_key: str, default_value: Optional[str] = None
    ) -> Optional[str]:
        """Retrieve the value of a given identifier

        Args:
            identifier_key (str): Key of the identifier
            default_value (str): An optional default value

        Returns:
            The value associated with the identifier.
            If the value associated with the identifier is empty and 'default_value' is
            provided, returns 'default_value'.
            If the identifier does not exist, returns default_value if provided, else 'None'.
        """
        return self._key.get_identifier(identifier_key, default_value)

    def add_metric(self, metric: Metric) -> None:
        """Adds a single Metric data point to this Object.

        Args:
            metric (Metric): A Metric data point to add to this Object.
        """
        self._metrics.append(metric)

    def add_metrics(self, metrics: List[Metric]) -> None:
        """Adds a list of Metric data points to this Object.

        Args:
            metrics (List[Metric]): A list of Metric data points to add to this Object.
        """
        for metric in metrics:
            self.add_metric(metric)

    def with_metric(self, *args: Any, **kwargs: Any) -> None:
        """Method that handles creating a :class:`Metric` data point, and adding to this Object.

        The signature matches :class:`Metric.__init__`.
        """
        self.add_metric(Metric(*args, **kwargs))

    def get_metric(self, key: str) -> List[Metric]:
        """

        Args:
         key (str): Metric key of the metric to return.

        Returns:
            All metrics matching the given key.
        """
        return list(filter(lambda metric: metric.key == key, self._metrics))

    def get_metric_values(self, key: str) -> List[float]:
        """

        Args:
            key (str): Metric key of the metric to return.

        Returns (List[float]): A list of the metric values in chronological order.
        """
        # find matching metrics
        metrics = self.get_metric(key)

        # sort metrics by timestamp from oldest  to newest
        metrics.sort(key=lambda metric: metric.timestamp)  # type: ignore

        return [m.value for m in metrics]

    def get_last_metric_value(self, key: str) -> Optional[float]:
        """

        Args:
            key (str) : Metric key of the metric to return.

        Returns:
            The latest value of the metric or None if no metric exists with the given key.
        """
        metrics = self.get_metric_values(key)

        if not metrics:
            return None
        else:
            return metrics[-1]

    def add_property(self, property_: Property) -> None:
        """Method that adds a single Property value to this Object

        Args:
            property_ (Property): A :class:`Property` value to add to this Object
        """
        self._properties.append(property_)

    def add_properties(self, properties: List[Property]) -> None:
        """Method that adds a list of Property values to this Object

        Args:
            properties (List[Property]): A list of :class:`Property` values to add to this Object
        """
        for property_ in properties:
            self.add_property(property_)

    def with_property(self, *args: Any, **kwargs: Any) -> None:
        """Method that handles creating a :class:`Property` value, and adding to this Object.

        The signature matches :class:`Property.__init__`.
        """
        self.add_property(Property(*args, **kwargs))

    def get_property(self, key: str) -> List[Property]:
        """

        Args:
            key (str): Property key of the property to return.

        Returns:
             All properties matching the given key
        """
        return list(filter(lambda property_: property_.key == key, self._properties))

    def get_property_values(self, key: str) -> List[str]:
        """

        Args:
            key (str): Property key of the property to return.

        Returns:
            A list of the property values in chronological order.
        """
        # find matching properties
        properties = self.get_property(key)

        # sort properties by timestamp from oldest  to newest
        properties.sort(key=lambda property_: property_.timestamp)  # type: ignore

        return [p.value for p in properties]

    def get_last_property_value(self, key: str) -> Optional[str | float]:
        """

        Args:
            key (str): Property key of the property to return.

        Returns:
             The latest value of the property or None if no property exists with the given key.
        """
        properties = self.get_property_values(key)

        if not properties:
            return None
        else:
            return properties[-1]

    def add_event(self, event: Event) -> None:
        """Method that adds a single Event to this Object

        Args:
            event: An :class:`Event` to add to this Object
        """
        self._events.add(event)

    def add_events(self, events: List[Event]) -> None:
        """Method that adds a list of Events to this Object

        Args:
            events (List[Event]): A list of :class:`Event` to add to this Object
        """
        for event in events:
            self.add_event(event)

    def with_event(self, *args: Any, **kwargs: Any) -> None:
        """Method that handles creating an :class:`Event`, and adding to this Object.

        The signature matches :class:`Event.__init__`.
        """
        self.add_event(Event(*args, **kwargs))

    def add_parent(self, parent: Object) -> None:
        """Method that adds a parent Object to this Object.

        This Object will also be added as a child to the parent.

        Relationship cycles are not permitted.

        Args:
            parent (Object): Parent :class:`Object`
        """
        self._parents.add(parent._key)
        parent._children.add(self._key)

    def add_parents(self, parents: List[Object]) -> None:
        """Method that adds a list of parent Objects to this Object.

        This Object will also be added as a child to each of the parents.

        Relationship cycles are not permitted.

        Args:
            parents (List[Object]): A list of parent :class:`Object`
        """
        for parent in parents:
            self.add_parent(parent)

    def get_parents(self) -> Set[Key]:
        """
        Returns:
         A set of all object keys that are parents of this object
        """
        return self._parents

    def add_child(self, child: Object) -> None:
        """Method that adds a child Object to this Object.

        This Object will also be added as a parent to the child.

        Relationship cycles are not permitted.

        Args:
            child (Object): Child :class:`Object`
        """
        self._updated_children = True
        self._children.add(child._key)
        child._parents.add(self._key)

    def add_children(self, children: List[Object]) -> None:
        """Method that adds a list of child Objects to this Object.

        This Object will also be added as a parent to each of the children.

        Relationship cycles are not permitted.

        Args:
            children (List[Object]): A list of child :class:`Object`
        """
        # We want to set this even in the case where the list is empty
        self._updated_children = True
        for child in children:
            self.add_child(child)

    def get_children(self) -> Set[Key]:
        """
        Returns:
            A set of all object keys that are children of this object
        """
        return self._children

    def has_content(self) -> bool:
        """
        Returns:
             True if the object contains any metrics, properties or events; False otherwise.
        """
        return bool(self._metrics) or bool(self._properties) or bool(self._events)

    def get_json(self) -> dict:
        """Get a JSON representation of this Object

        Returns a JSON representation of this Object in the format required by vROps.

        Returns:
             A JSON representation of this Object
        """
        return {
            "key": self._key.get_json(),
            "metrics": [metric.get_json() for metric in self._metrics],
            "properties": [prop.get_json() for prop in self._properties],
            "events": [event.get_json() for event in self._events],
        }
