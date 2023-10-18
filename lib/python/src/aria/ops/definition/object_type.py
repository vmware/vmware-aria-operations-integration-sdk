#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import OrderedDict
from typing import Optional
from typing import Union

from aria.ops.definition.assertions import validate_key
from aria.ops.definition.exceptions import DuplicateKeyException
from aria.ops.definition.group import GroupType
from aria.ops.definition.parameter import EnumParameter
from aria.ops.definition.parameter import IntParameter
from aria.ops.definition.parameter import Parameter
from aria.ops.definition.parameter import StringParameter


class ObjectType(GroupType):  # type: ignore
    def __init__(self, key: str, label: Optional[str] = None):
        """
        Create a new object type definition

        Args:
            key (str): The key of the object type
            label (Optional[str]): Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        """
        self.key = validate_key(key, "Object type")
        self.label = label
        if label is None:
            self.label = key
        self.identifiers: dict = OrderedDict()
        super().__init__()

    def define_string_identifier(
        self,
        key: str,
        label: Optional[str] = None,
        required: bool = True,
        is_part_of_uniqueness: bool = True,
        default: Optional[str] = None,
    ) -> ObjectType:
        """
        Create a new string identifier and apply it to this object type definition.
        All identifiers marked as 'part of uniqueness' are used to determine object identification. If none exist, the
        object name will be used for identification.

        Args:
            key (str): Used to identify the parameter.
            label (Optinal[str]): Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
            required (bool): True if this parameter is required. Defaults to True.
            is_part_of_uniqueness (bool): True if the parameter should be used for object identification. Defaults to True.
            default (Optional[str]): The default value of the parameter.

        Returns:
             The created String Identifier.
        """
        parameter = StringParameter(
            key,
            label,
            required=required,
            advanced=not is_part_of_uniqueness,
            default=default,
            display_order=len(self.identifiers),
        )
        self.add_identifier(parameter)
        return self

    def define_int_identifier(
        self,
        key: str,
        label: Optional[str] = None,
        required: bool = True,
        is_part_of_uniqueness: bool = True,
        default: Optional[int] = None,
    ) -> ObjectType:
        """
        Create a new int identifier and apply it to this object type definition.
        All identifiers marked 'part of uniqueness' are used to determine object identification. If none exist, the
        object name will be used for identification.
        Args:
            key (str): Used to identify the parameter.
            label (Optional[str]): Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
            required (bool): True if this parameter is required. Defaults to True.
            is_part_of_uniqueness (bool): True if the parameter should be used for object identification. Defaults to True.
            default ([Optional[int]): The default value of the parameter.

        Returns:
             The created Int Identifier.
        """
        parameter = IntParameter(
            key,
            label,
            required=required,
            advanced=not is_part_of_uniqueness,
            default=default,
            display_order=len(self.identifiers),
        )
        self.add_identifier(parameter)
        return self

    def define_enum_identifier(
        self,
        key: str,
        values: list[Union[str, tuple[str, str]]],
        label: Optional[str] = None,
        required: bool = True,
        is_part_of_uniqueness: bool = True,
        default: Optional[str] = None,
    ) -> ObjectType:
        """
        Create a new enum identifier and apply it to this object type definition.
        All identifiers marked as 'part of uniqueness' are used to determine object identification. If none exist, the
        object name will be used for identification.

        Args:
            key (str): Used to identify the parameter.
            values (list[Union[str, tuple[str, str]]]): An array containing all enum values. If 'default' is specified and not part of this array, it
            will be added as an additional enum value (values are case-sensitive). Enum values are not localizable.
            label [Optinal[str]): Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
            required (bool): True if this parameter is required. Defaults to True.
            is_part_of_uniqueness (bool): True if the parameter should be used for object identification. Defaults to True.
            default (Optional[str]): The default value of the parameter.

        Returns:
            The created Enum Identifier.
        """
        parameter = EnumParameter(
            key,
            values,
            label,
            required=required,
            advanced=not is_part_of_uniqueness,
            default=default,
            display_order=len(self.identifiers),
        )
        self.add_identifier(parameter)
        return self

    def add_identifiers(self, identifiers: list[Parameter]) -> None:
        """

        Args:
            identifiers: A list of identifiers to add to this object type
        """
        for identifier in identifiers:
            self.add_identifier(identifier)

    def add_identifier(self, identifier: Parameter) -> None:
        """
        Add an identifier to this object type. All 'identifying' identifiers are used to determine object uniqueness.
        If no 'identifying' identifiers exist, they object name will be used for uniqueness.

        Args:
            identifier (Parameter): The identifier to add to the object type definition.
        """
        key = identifier.key
        if key in self.identifiers:
            raise DuplicateKeyException(
                f"Identifier with key {key} already exists in object type {self.key}."
            )
        self.identifiers[key] = identifier

    def to_json(self) -> dict:
        return {  # type: ignore
            "key": self.key,
            "label": self.label,
            "identifiers": [
                identifier.to_json() for identifier in self.identifiers.values()
            ],
        } | super().to_json()
