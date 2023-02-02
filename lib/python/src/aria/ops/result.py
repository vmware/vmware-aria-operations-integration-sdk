#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import sys
from enum import auto
from typing import List
from typing import NewType
from typing import Optional

from aenum import Enum
from aria.ops.definition.adapter_definition import AdapterDefinition
from aria.ops.object import Identifier
from aria.ops.object import Key
from aria.ops.object import Object
from aria.ops.pipe_utils import write_to_pipe


class ObjectKeyAlreadyExistsException(Exception):
    """Exception when two objects with the same Key are added to the same
    :class:`Result`"""

    pass


class TestResult:
    """Class for managing the results of an adapter instance connection test"""

    def __init__(self) -> None:
        """Initializes a Result"""
        self._error_message: Optional[str] = None

    def is_success(self) -> bool:
        """

        :return: True if the TestResult represents a successful test
        """
        return self._error_message is None

    def with_error(self, error_message: str) -> None:
        """Set the adapter instance connection test to failed, and display the given
        error message.

        If this method is called multiple times, only the most recent error message
        will be recorded. If error_message is set, the test is considered failed.

        :param error_message: A string containing the error message
        :return: None
        """
        self._error_message = error_message

    def get_json(self) -> dict:
        """Get a JSON representation of this TestResult

        Returns a JSON representation of this TestResult in the format required by
        Aria Operations, indicating either a successful test, or a failed test with
        error message.

        :return: A JSON representation of this TestResult
        """
        if self.is_success():
            return {}
        else:
            return {"errorMessage": self._error_message}

    def send_results(self, output_pipe: str = sys.argv[-1]) -> None:
        """Opens the output pipe and sends results directly back to the server

        This method can only be called once per collection.
        """
        # The server always invokes methods with the output file as the last argument
        write_to_pipe(output_pipe, self.get_json())


class EndpointResult:
    """Class for managing the results of an adapter instance get endpoint URLs call

    The result of this should be a set of urls that the adapter will connect to.
    Aria Operations will then attempt to connect to each of these urls securely,
    and prompt the user to accept or reject the certificate presented by each URL.

    """

    def __init__(self) -> None:
        """Initializes an EndpointResult"""
        self.endpoints: list[str] = []

    def with_endpoint(self, endpoint_url: str) -> None:
        """Adds an endpoint to the list of endpoints Aria Operations will test for
        certificate validation.

        If this method is called multiple times, each url will be called by Aria
        Operations.

        :param endpoint_url: A string containing the url

        :return: None
        """
        self.endpoints.append(endpoint_url)

    def get_json(self) -> dict:
        """Get a JSON representation of this EndpointResult

        Returns a JSON representation of this EndpointResult in the format required
        by Aria Operations.

        :return: A JSON representation of this EndpointResult
        """
        return {"endpointUrls": self.endpoints}

    def send_results(self, output_pipe: str = sys.argv[-1]) -> None:
        """Opens the output pipe and sends results directly back to the server

        This method can only be called once per collection.
        """
        # The server always invokes methods with the output file as the last argument
        write_to_pipe(output_pipe, self.get_json())


RelationshipUpdateMode = NewType("RelationshipUpdateMode", int)


class RelationshipUpdateModes(Enum):  # type: ignore
    """
    If 'update_relationships' is 'ALL', all relationships between objects are
    returned.

    If 'update_relationships' is 'None', no relationships will be returned.

    If 'update_relationships' is 'AUTO' (or not explicitly set), then all
    relationships are returned _if and only if at least one object has set
    relationships_.

    If 'update_relationships' is 'PER_OBJECT', then only objects with updated
    relationships will be returned. Note: Any object that has not been updated
    will retain existing relationships. This means that to remove all
    relationships from an object (without setting any new relationships), the
    adapter must call 'add_children' on the object with an empty collection of
    children.

    If an object's relationships are returned, but the object has no current
    relationships, then any previously-existing relationships will be removed.

    If an object's relationships are not returned, then any previously-existing
    relationships will remain present in Aria Operations.

    The default behavior makes it easy to skip collecting relationships for a
    collection without overwriting previously-collected relationships, e.g.,
    for performance reasons.
    """

    ALL = RelationshipUpdateMode(1)
    NONE = RelationshipUpdateMode(2)
    AUTO = RelationshipUpdateMode(3)
    PER_OBJECT = RelationshipUpdateMode(4)


class CollectResult:
    """Class for managing a collection of Aria Operations Objects"""

    def __init__(
        self,
        obj_list: Optional[list[Object]] = None,
        target_definition: AdapterDefinition = None,
    ) -> None:
        """Initializes a Result

        A result contains objects, which can be added at initialization or later.
        Each object has a key containing one or more identifiers plus the object type
        and adapter type. Keys must be unique across objects in a Result.

        :param obj_list: an optional list of objects to send to Aria Operations.
        Objects can be added later using add_object

        :param target_definition: an optional description of the returned objects,
        used for validation purposes
        """
        self.objects: dict[Key, Object] = {}
        if type(obj_list) is list:
            self.add_objects(obj_list)
        self.definition: AdapterDefinition = target_definition
        self.adapter_type = None
        if self.definition:
            self.adapter_type = self.definition.key
        self._error_message: Optional[str] = None
        self.update_relationships: RelationshipUpdateMode = RelationshipUpdateModes.AUTO

    def _object_is_external(self, obj: Object) -> bool:
        return bool(self.adapter_type) and not obj.adapter_type() == self.adapter_type

    def object(
        self,
        adapter_kind: str,
        object_kind: str,
        name: str,
        identifiers: Optional[list[Identifier]] = None,
    ) -> Object:
        """Get or create the object with key specified by adapter_kind, object_kind,
        name, and identifiers.

        This is the preferred method for creating new Objects. If this method is used
        exclusively, all object references with the same key will point to the same
        object.

        If an object with the same key already exists in the result, return that
        object, otherwise create a new object, add it to the result, and return it.
        See discussion on keys in the documentation for the :class:`object.Key` class.

        If this method is used to create an object, it does not need to be added
        later using `add_object` (or `add_objects`)

        :param adapter_kind: The adapter kind of the object
        :param object_kind: The resource kind of the object
        :param name: The name of the object
        :param identifiers:
        :return: The object with the given key
        """
        obj = Object(Key(adapter_kind, object_kind, name, identifiers))
        return self.objects.setdefault(obj.get_key(), obj)

    def get_object(self, obj_key: Key) -> Optional[Object]:
        """Get and return the object corresponding to the given key, if it exists

        :param obj_key: The object key to search for
        :return: The object with the given key, or None if the key is not in the result
        """
        return self.objects.get(obj_key, None)

    def get_objects_by_type(
        self, object_type: str, adapter_type: Optional[str] = None
    ) -> List[Object]:
        """Returns all objects with the given type. If adapter_type is present,
        the objects must also be from the given adapter type.

        :param object_type: The object type to return
        :param adapter_type: The adapter type of the objects to return
        :return: A list of objects matching the object type and adapter type
        """
        return [
            obj
            for obj in self.objects.values()
            if obj.adapter_type() == object_type
            and (adapter_type is None or adapter_type == obj.adapter_type())
        ]

    def add_object(self, obj: Object) -> Object:
        """Adds the given object to the Result and returns it.

        Adds the given object to the Result and returns it. A different object with
        the same key cannot already exist in the Result. If it does,
        an :class:`ObjectKeyAlreadyExistsException` will be raised.

        :param obj: An object to add to the Result
        :return: The object
        :raises: ObjectKeyAlreadyExistsException if a different object with the same key
        already exists in the Result
        """
        o = self.objects.setdefault(obj.get_key(), obj)
        if o is obj:
            return o
        raise ObjectKeyAlreadyExistsException(
            f"A different object with key {obj.get_key()} already exists."
        )

    def add_objects(self, obj_list: list[Object]) -> None:
        """Adds the given objects to the Result and returns it.

        Adds the given objects to the Result. A different object with the same key
        cannot already exist in the Result. If it does, an
        :class:`ObjectKeyAlreadyExistsException` will be raised.

        :param obj_list: A list of objects to add to the Result
        :return: The object
        :raises: ObjectKeyAlreadyExistsException if a different object with the same
        key already exists in the Result
        """
        for obj in obj_list:
            self.add_object(obj)

    def with_error(self, error_message: str) -> None:
        """Set the Adapter Instance to an error state with the provided message.

        If this method is called multiple times, only the most recent error message
        will be recorded. If error_message is set, no results (objects, relationships)
        will be returned.

        :param error_message: A string containing the error message
        :return: None
        """
        self._error_message = error_message

    def get_json(self) -> dict:
        """Get a JSON representation of this Result

        Returns a JSON representation of this Result in the format required by Aria
        Operations. The representation includes all objects (including the object's
        events, properties, and metrics) in the Result. Relationships are returned
        following the update_relationships flag (See RelationshipUpdateMode).

        :return: A JSON representation of this Result
        """
        if self._error_message is None:
            result = {
                "result": [
                    obj.get_json()
                    for obj in self.objects.values()
                    if not self._object_is_external(obj) or obj.has_content()
                ],
                "relationships": [],
                "nonExistingObjects": [],
            }
            if (
                self.update_relationships == RelationshipUpdateModes.ALL
                or self.update_relationships == RelationshipUpdateModes.PER_OBJECT
                or (
                    self.update_relationships == RelationshipUpdateModes.AUTO
                    and any([obj._updated_children for obj in self.objects.values()])
                )
            ):
                result.update(
                    {
                        "relationships": [
                            {
                                "parent": obj.get_key().get_json(),
                                "children": [
                                    child_key.get_json()
                                    for child_key in obj.get_children()
                                ],
                            }
                            for obj in self.objects.values()
                            if (
                                self.update_relationships
                                == RelationshipUpdateModes.PER_OBJECT
                                and obj._updated_children
                            )
                            or not self.update_relationships
                            == RelationshipUpdateModes.PER_OBJECT
                        ],
                    }
                )
            return result
        else:
            return {"errorMessage": self._error_message}

    def send_results(self, output_pipe: str = sys.argv[-1]) -> None:
        """Opens the output pipe and sends results directly back to the server

        This method can only be called once per collection.
        """
        # The server always invokes methods with the output file as the last argument
        write_to_pipe(output_pipe, self.get_json())
