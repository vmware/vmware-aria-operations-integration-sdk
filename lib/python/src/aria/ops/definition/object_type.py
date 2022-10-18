#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import OrderedDict

from aria.ops.definition.assertions import validate_key
from aria.ops.definition.exceptions import DuplicateKeyException
from aria.ops.definition.group import GroupType
from aria.ops.definition.parameter import EnumParameter, IntParameter, StringParameter, Parameter


class ObjectType(GroupType):
    def __init__(self,
                 key: str,
                 label: str = None):
        """
        Create a new object type definition
        :param key: The key of the object type
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        """
        self.key = validate_key(key, "Object type")
        self.label = label
        if label is None:
            self.label = key
        self.identifiers = OrderedDict()
        super().__init__()

    def define_string_identifier(self, key: str, label: str = None, required: bool = True, is_part_of_uniqueness: bool = True,
                                 default: str = None) -> ObjectType:
        """
        Create a new string identifier and apply it to this object type definition.
        All identifiers marked as 'part of uniqueness' are used to determine object identification. If none exist, the 
        object name will be used for identification.
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param required: True if this parameter is required. Defaults to True.
        :param is_part_of_uniqueness: True if the parameter should be used for object identification. Defaults to True.
        :param default: The default value of the parameter.
        :return The created String Identifier.
        """
        parameter = StringParameter(key, label, required=required, advanced=not is_part_of_uniqueness, default=default,
                                    display_order=len(self.identifiers))
        self.add_identifier(parameter)
        return self

    def define_int_identifier(self, key: str, label: str = None, required: bool = True, is_part_of_uniqueness: bool = True,
                              default: int = None) -> ObjectType:
        """
        Create a new int identifier and apply it to this object type definition.
        All identifiers marked 'part of uniqueness' are used to determine object identification. If none exist, the 
        object name will be used for identification.
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param required: True if this parameter is required. Defaults to True.
        :param is_part_of_uniqueness: True if the parameter should be used for object identification. Defaults to True.
        :param default: The default value of the parameter.
        :return The created Int Identifier.
        """
        parameter = IntParameter(key, label, required=required, advanced=not is_part_of_uniqueness, default=default,
                                 display_order=len(self.identifiers))
        self.add_identifier(parameter)
        return self

    def define_enum_identifier(self, key: str, values: list[str], label: str = None, required: bool = True,
                               is_part_of_uniqueness: bool = True, default: str = None) -> ObjectType:
        """
        Create a new enum identifier and apply it to this object type definition.
        All identifiers marked as 'part of uniqueness' are used to determine object identification. If none exist, the 
        object name will be used for identification.
        :param key: Used to identify the parameter.
        :param values: An array containing all enum values. If 'default' is specified and not part of this array, it
               will be added as an additional enum value (values are case-sensitive). Enum values are not localizable.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param required: True if this parameter is required. Defaults to True.
        :param is_part_of_uniqueness: True if the parameter should be used for object identification. Defaults to True.
        :param default: The default value of the parameter.
        :return The created Enum Identifier.
        """
        parameter = EnumParameter(key, values, label, required=required, advanced=not is_part_of_uniqueness, default=default,
                                  display_order=len(self.identifiers))
        self.add_identifier(parameter)
        return self

    def add_identifiers(self, identifiers: list[Parameter]):
        """
        :param identifiers: A list of identifiers to add to this object type
        :return: None
        """
        for identifier in identifiers:
            self.add_identifier(identifier)

    def add_identifier(self, identifier: Parameter):
        """
        Add an identifier to this object type. All 'identifying' identifiers are used to determine object uniqueness.
        If no 'identifying' identifiers exist, they object name will be used for uniqueness.
        :param identifier: The identifier to add to the object type definition.
        :return: None
        """
        key = identifier.key
        if key in self.identifiers:
            raise DuplicateKeyException(f"Identifier with key {key} already exists in object type {self.key}.")
        self.identifiers[key] = identifier

    def to_json(self):
        return {
                   "key": self.key,
                   "label": self.label,
                   "identifiers": [identifier.to_json() for identifier in self.identifiers.values()],
               } | super().to_json()
