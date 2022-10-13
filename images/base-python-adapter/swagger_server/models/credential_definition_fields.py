# coding: utf-8

#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class CredentialDefinitionFields(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    def __init__(self, key: str=None, label: str=None, required: bool=True, password: bool=False, enum: bool=False, enum_values: List[str]=None, default: str=None, display_order: int=None, type: str='string'):  # noqa: E501
        """CredentialDefinitionFields - a model defined in Swagger

        :param key: The key of this CredentialDefinitionFields.  # noqa: E501
        :type key: str
        :param label: The label of this CredentialDefinitionFields.  # noqa: E501
        :type label: str
        :param required: The required of this CredentialDefinitionFields.  # noqa: E501
        :type required: bool
        :param password: The password of this CredentialDefinitionFields.  # noqa: E501
        :type password: bool
        :param enum: The enum of this CredentialDefinitionFields.  # noqa: E501
        :type enum: bool
        :param enum_values: The enum_values of this CredentialDefinitionFields.  # noqa: E501
        :type enum_values: List[str]
        :param default: The default of this CredentialDefinitionFields.  # noqa: E501
        :type default: str
        :param display_order: The display_order of this CredentialDefinitionFields.  # noqa: E501
        :type display_order: int
        :param type: The type of this CredentialDefinitionFields.  # noqa: E501
        :type type: str
        """
        self.swagger_types = {
            'key': str,
            'label': str,
            'required': bool,
            'password': bool,
            'enum': bool,
            'enum_values': List[str],
            'default': str,
            'display_order': int,
            'type': str
        }

        self.attribute_map = {
            'key': 'key',
            'label': 'label',
            'required': 'required',
            'password': 'password',
            'enum': 'enum',
            'enum_values': 'enum_values',
            'default': 'default',
            'display_order': 'display_order',
            'type': 'type'
        }
        self._key = key
        self._label = label
        self._required = required
        self._password = password
        self._enum = enum
        self._enum_values = enum_values
        self._default = default
        self._display_order = display_order
        self._type = type

    @classmethod
    def from_dict(cls, dikt) -> 'CredentialDefinitionFields':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The CredentialDefinition_fields of this CredentialDefinitionFields.  # noqa: E501
        :rtype: CredentialDefinitionFields
        """
        return util.deserialize_model(dikt, cls)

    @property
    def key(self) -> str:
        """Gets the key of this CredentialDefinitionFields.


        :return: The key of this CredentialDefinitionFields.
        :rtype: str
        """
        return self._key

    @key.setter
    def key(self, key: str):
        """Sets the key of this CredentialDefinitionFields.


        :param key: The key of this CredentialDefinitionFields.
        :type key: str
        """

        self._key = key

    @property
    def label(self) -> str:
        """Gets the label of this CredentialDefinitionFields.


        :return: The label of this CredentialDefinitionFields.
        :rtype: str
        """
        return self._label

    @label.setter
    def label(self, label: str):
        """Sets the label of this CredentialDefinitionFields.


        :param label: The label of this CredentialDefinitionFields.
        :type label: str
        """

        self._label = label

    @property
    def required(self) -> bool:
        """Gets the required of this CredentialDefinitionFields.


        :return: The required of this CredentialDefinitionFields.
        :rtype: bool
        """
        return self._required

    @required.setter
    def required(self, required: bool):
        """Sets the required of this CredentialDefinitionFields.


        :param required: The required of this CredentialDefinitionFields.
        :type required: bool
        """

        self._required = required

    @property
    def password(self) -> bool:
        """Gets the password of this CredentialDefinitionFields.


        :return: The password of this CredentialDefinitionFields.
        :rtype: bool
        """
        return self._password

    @password.setter
    def password(self, password: bool):
        """Sets the password of this CredentialDefinitionFields.


        :param password: The password of this CredentialDefinitionFields.
        :type password: bool
        """

        self._password = password

    @property
    def enum(self) -> bool:
        """Gets the enum of this CredentialDefinitionFields.


        :return: The enum of this CredentialDefinitionFields.
        :rtype: bool
        """
        return self._enum

    @enum.setter
    def enum(self, enum: bool):
        """Sets the enum of this CredentialDefinitionFields.


        :param enum: The enum of this CredentialDefinitionFields.
        :type enum: bool
        """

        self._enum = enum

    @property
    def enum_values(self) -> List[str]:
        """Gets the enum_values of this CredentialDefinitionFields.


        :return: The enum_values of this CredentialDefinitionFields.
        :rtype: List[str]
        """
        return self._enum_values

    @enum_values.setter
    def enum_values(self, enum_values: List[str]):
        """Sets the enum_values of this CredentialDefinitionFields.


        :param enum_values: The enum_values of this CredentialDefinitionFields.
        :type enum_values: List[str]
        """

        self._enum_values = enum_values

    @property
    def default(self) -> str:
        """Gets the default of this CredentialDefinitionFields.


        :return: The default of this CredentialDefinitionFields.
        :rtype: str
        """
        return self._default

    @default.setter
    def default(self, default: str):
        """Sets the default of this CredentialDefinitionFields.


        :param default: The default of this CredentialDefinitionFields.
        :type default: str
        """

        self._default = default

    @property
    def display_order(self) -> int:
        """Gets the display_order of this CredentialDefinitionFields.


        :return: The display_order of this CredentialDefinitionFields.
        :rtype: int
        """
        return self._display_order

    @display_order.setter
    def display_order(self, display_order: int):
        """Sets the display_order of this CredentialDefinitionFields.


        :param display_order: The display_order of this CredentialDefinitionFields.
        :type display_order: int
        """

        self._display_order = display_order

    @property
    def type(self) -> str:
        """Gets the type of this CredentialDefinitionFields.


        :return: The type of this CredentialDefinitionFields.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type: str):
        """Sets the type of this CredentialDefinitionFields.


        :param type: The type of this CredentialDefinitionFields.
        :type type: str
        """

        self._type = type