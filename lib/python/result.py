__author__ = 'VMware, Inc.'
__copyright__ = 'Copyright 2022 VMware, Inc. All rights reserved.'

from object import Object, Key


class ObjectKeyAlreadyExistsException(Exception):
    pass


class Result:
    """Class for managing a collection of vROps Objects
    """

    def __init__(self, objects=None, target_definition=None):
        """Initializes a Result

        A result contains objects, which can be added at initialization or later. Each object has a key containing one
        or more identifiers plus the object type and adapter type. Keys must be unique across objects in a Result.

        :param objects: an optional list of objects to send to vROps. Objects can be added later using add_object
        :param target_definition: an optional description of the returned objects, used for validation purposes
        """
        if objects is None:
            objects = {}
        self.objects = {object_.get_key(): object_ for object_ in objects}

    def object(self, adapter_kind: str, object_kind: str, name: str, identifiers=None) -> Object:
        """Get or create the object with key specified by adapter_kind, object_kind, name, and identifiers.

        This is the preferred method for creating new Objects. If this method is used exclusively, all object references
        with the same key will point to the same object.

        If an object with the same key already exists in the result, return that object, otherwise create a new object,
        add it to the result, and return it. See discussion on keys in the documentation for the :class:`object.Key`
        class.

        :param adapter_kind: The adapter kind of the object
        :param object_kind: The resource kind of the object
        :param name: The name of the object
        :param identifiers:
        :return: The object with the given key
        """
        obj = Object(Key(adapter_kind, object_kind, name, identifiers))
        return self.objects.setdefault(obj._key, obj)

    def add_object(self, obj: Object):
        """Adds the given object to the Result and returns it.

        Adds the given object to the Result and returns it. A different object with the same key cannot already exist
        in the Result. If it does, an :class:`ObjectKeyAlreadyExistsException` will be raised.

        :param obj: An object to add to the Result
        :return: The object
        :raises: KeyAlreadyExistsException if a different object with the same key already exists in the Result
        """
        o = self.objects.setdefault(obj._key, obj)
        if o is obj:
            return o
        raise ObjectKeyAlreadyExistsException(f"A different object with key {obj._key} already exists.")

    def get_json(self):
        """Get a JSON representation of this Result

        Returns a JSON representation of this Result in the format required by vROps. The representation includes all
        objects (including the object's events, properties, and metrics) in the Result, and all relationships between
        objects.

        :return: A JSON representation of this Result
        """
        return {
            "result": [obj.get_json() for obj in self.objects],
            "relationships": [
                {
                    "parent": obj.get_key(),
                    "children": [child.get_key() for child in obj.children]
                } for obj in self.objects
            ],
            "nonExistingObjects": [],
            "errorMessage": None,
        }
