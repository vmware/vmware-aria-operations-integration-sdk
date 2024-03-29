# coding: utf-8
#  Copyright 2022-2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import absolute_import

from datetime import date
from datetime import datetime
from typing import Dict
from typing import List

from swagger_server import util
from swagger_server.models.base_model_ import Model
from swagger_server.models.credential_definition_enum_values import (
    CredentialDefinitionEnumValues,
)  # noqa: F401,E501


class IdentifierDefinition(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(
        self,
        key: str = None,
        label: str = None,
        description: str = None,
        required: bool = True,
        ident_type: int = 1,
        enum: bool = False,
        enum_values: List[CredentialDefinitionEnumValues] = None,
        display_order: int = None,
        type: str = None,
        length: int = None,
        default: str = None,
    ):  # noqa: E501
        """IdentifierDefinition - a model defined in Swagger

        :param key: The key of this IdentifierDefinition.  # noqa: E501
        :type key: str
        :param label: The label of this IdentifierDefinition.  # noqa: E501
        :type label: str
        :param description: The description of this IdentifierDefinition.  # noqa: E501
        :type description: str
        :param required: The required of this IdentifierDefinition.  # noqa: E501
        :type required: bool
        :param ident_type: The ident_type of this IdentifierDefinition.  # noqa: E501
        :type ident_type: int
        :param enum: The enum of this IdentifierDefinition.  # noqa: E501
        :type enum: bool
        :param enum_values: The enum_values of this IdentifierDefinition.  # noqa: E501
        :type enum_values: List[CredentialDefinitionEnumValues]
        :param display_order: The display_order of this IdentifierDefinition.  # noqa: E501
        :type display_order: int
        :param type: The type of this IdentifierDefinition.  # noqa: E501
        :type type: str
        :param length: The length of this IdentifierDefinition.  # noqa: E501
        :type length: int
        :param default: The default of this IdentifierDefinition.  # noqa: E501
        :type default: str
        """
        self.swagger_types = {
            "key": str,
            "label": str,
            "description": str,
            "required": bool,
            "ident_type": int,
            "enum": bool,
            "enum_values": List[CredentialDefinitionEnumValues],
            "display_order": int,
            "type": str,
            "length": int,
            "default": str,
        }

        self.attribute_map = {
            "key": "key",
            "label": "label",
            "description": "description",
            "required": "required",
            "ident_type": "ident_type",
            "enum": "enum",
            "enum_values": "enum_values",
            "display_order": "display_order",
            "type": "type",
            "length": "length",
            "default": "default",
        }
        self._key = key
        self._label = label
        self._description = description
        self._required = required
        self._ident_type = ident_type
        self._enum = enum
        self._enum_values = enum_values
        self._display_order = display_order
        self._type = type
        self._length = length
        self._default = default

    @classmethod
    def from_dict(cls, dikt) -> "IdentifierDefinition":
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The IdentifierDefinition of this IdentifierDefinition.  # noqa: E501
        :rtype: IdentifierDefinition
        """
        return util.deserialize_model(dikt, cls)

    @property
    def key(self) -> str:
        """Gets the key of this IdentifierDefinition.


        :return: The key of this IdentifierDefinition.
        :rtype: str
        """
        return self._key

    @key.setter
    def key(self, key: str):
        """Sets the key of this IdentifierDefinition.


        :param key: The key of this IdentifierDefinition.
        :type key: str
        """
        if key is None:
            raise ValueError(
                "Invalid value for `key`, must not be `None`"
            )  # noqa: E501

        self._key = key

    @property
    def label(self) -> str:
        """Gets the label of this IdentifierDefinition.


        :return: The label of this IdentifierDefinition.
        :rtype: str
        """
        return self._label

    @label.setter
    def label(self, label: str):
        """Sets the label of this IdentifierDefinition.


        :param label: The label of this IdentifierDefinition.
        :type label: str
        """
        if label is None:
            raise ValueError(
                "Invalid value for `label`, must not be `None`"
            )  # noqa: E501

        self._label = label

    @property
    def description(self) -> str:
        """Gets the description of this IdentifierDefinition.


        :return: The description of this IdentifierDefinition.
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description: str):
        """Sets the description of this IdentifierDefinition.


        :param description: The description of this IdentifierDefinition.
        :type description: str
        """

        self._description = description

    @property
    def required(self) -> bool:
        """Gets the required of this IdentifierDefinition.


        :return: The required of this IdentifierDefinition.
        :rtype: bool
        """
        return self._required

    @required.setter
    def required(self, required: bool):
        """Sets the required of this IdentifierDefinition.


        :param required: The required of this IdentifierDefinition.
        :type required: bool
        """
        if required is None:
            raise ValueError(
                "Invalid value for `required`, must not be `None`"
            )  # noqa: E501

        self._required = required

    @property
    def ident_type(self) -> int:
        """Gets the ident_type of this IdentifierDefinition.


        :return: The ident_type of this IdentifierDefinition.
        :rtype: int
        """
        return self._ident_type

    @ident_type.setter
    def ident_type(self, ident_type: int):
        """Sets the ident_type of this IdentifierDefinition.


        :param ident_type: The ident_type of this IdentifierDefinition.
        :type ident_type: int
        """
        if ident_type is None:
            raise ValueError(
                "Invalid value for `ident_type`, must not be `None`"
            )  # noqa: E501

        self._ident_type = ident_type

    @property
    def enum(self) -> bool:
        """Gets the enum of this IdentifierDefinition.


        :return: The enum of this IdentifierDefinition.
        :rtype: bool
        """
        return self._enum

    @enum.setter
    def enum(self, enum: bool):
        """Sets the enum of this IdentifierDefinition.


        :param enum: The enum of this IdentifierDefinition.
        :type enum: bool
        """
        if enum is None:
            raise ValueError(
                "Invalid value for `enum`, must not be `None`"
            )  # noqa: E501

        self._enum = enum

    @property
    def enum_values(self) -> List[CredentialDefinitionEnumValues]:
        """Gets the enum_values of this IdentifierDefinition.


        :return: The enum_values of this IdentifierDefinition.
        :rtype: List[CredentialDefinitionEnumValues]
        """
        return self._enum_values

    @enum_values.setter
    def enum_values(self, enum_values: List[CredentialDefinitionEnumValues]):
        """Sets the enum_values of this IdentifierDefinition.


        :param enum_values: The enum_values of this IdentifierDefinition.
        :type enum_values: List[CredentialDefinitionEnumValues]
        """

        self._enum_values = enum_values

    @property
    def display_order(self) -> int:
        """Gets the display_order of this IdentifierDefinition.


        :return: The display_order of this IdentifierDefinition.
        :rtype: int
        """
        return self._display_order

    @display_order.setter
    def display_order(self, display_order: int):
        """Sets the display_order of this IdentifierDefinition.


        :param display_order: The display_order of this IdentifierDefinition.
        :type display_order: int
        """
        if display_order is None:
            raise ValueError(
                "Invalid value for `display_order`, must not be `None`"
            )  # noqa: E501

        self._display_order = display_order

    @property
    def type(self) -> str:
        """Gets the type of this IdentifierDefinition.


        :return: The type of this IdentifierDefinition.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type: str):
        """Sets the type of this IdentifierDefinition.


        :param type: The type of this IdentifierDefinition.
        :type type: str
        """
        if type is None:
            raise ValueError(
                "Invalid value for `type`, must not be `None`"
            )  # noqa: E501

        self._type = type

    @property
    def length(self) -> int:
        """Gets the length of this IdentifierDefinition.


        :return: The length of this IdentifierDefinition.
        :rtype: int
        """
        return self._length

    @length.setter
    def length(self, length: int):
        """Sets the length of this IdentifierDefinition.


        :param length: The length of this IdentifierDefinition.
        :type length: int
        """

        self._length = length

    @property
    def default(self) -> str:
        """Gets the default of this IdentifierDefinition.


        :return: The default of this IdentifierDefinition.
        :rtype: str
        """
        return self._default

    @default.setter
    def default(self, default: str):
        """Sets the default of this IdentifierDefinition.


        :param default: The default of this IdentifierDefinition.
        :type default: str
        """

        self._default = default
