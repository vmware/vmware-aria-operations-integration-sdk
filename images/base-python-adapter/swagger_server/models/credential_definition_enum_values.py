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


class CredentialDefinitionEnumValues(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(
        self, key: str = None, label: str = None, display_order: int = None
    ):  # noqa: E501
        """CredentialDefinitionEnumValues - a model defined in Swagger

        :param key: The key of this CredentialDefinitionEnumValues.  # noqa: E501
        :type key: str
        :param label: The label of this CredentialDefinitionEnumValues.  # noqa: E501
        :type label: str
        :param display_order: The display_order of this CredentialDefinitionEnumValues.  # noqa: E501
        :type display_order: int
        """
        self.swagger_types = {"key": str, "label": str, "display_order": int}

        self.attribute_map = {
            "key": "key",
            "label": "label",
            "display_order": "display_order",
        }
        self._key = key
        self._label = label
        self._display_order = display_order

    @classmethod
    def from_dict(cls, dikt) -> "CredentialDefinitionEnumValues":
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The CredentialDefinition_enum_values of this CredentialDefinitionEnumValues.  # noqa: E501
        :rtype: CredentialDefinitionEnumValues
        """
        return util.deserialize_model(dikt, cls)

    @property
    def key(self) -> str:
        """Gets the key of this CredentialDefinitionEnumValues.


        :return: The key of this CredentialDefinitionEnumValues.
        :rtype: str
        """
        return self._key

    @key.setter
    def key(self, key: str):
        """Sets the key of this CredentialDefinitionEnumValues.


        :param key: The key of this CredentialDefinitionEnumValues.
        :type key: str
        """

        self._key = key

    @property
    def label(self) -> str:
        """Gets the label of this CredentialDefinitionEnumValues.


        :return: The label of this CredentialDefinitionEnumValues.
        :rtype: str
        """
        return self._label

    @label.setter
    def label(self, label: str):
        """Sets the label of this CredentialDefinitionEnumValues.


        :param label: The label of this CredentialDefinitionEnumValues.
        :type label: str
        """

        self._label = label

    @property
    def display_order(self) -> int:
        """Gets the display_order of this CredentialDefinitionEnumValues.


        :return: The display_order of this CredentialDefinitionEnumValues.
        :rtype: int
        """
        return self._display_order

    @display_order.setter
    def display_order(self, display_order: int):
        """Sets the display_order of this CredentialDefinitionEnumValues.


        :param display_order: The display_order of this CredentialDefinitionEnumValues.
        :type display_order: int
        """

        self._display_order = display_order
