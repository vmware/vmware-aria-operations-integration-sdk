# coding: utf-8

#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class AttributeDefinition(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    def __init__(self, key: str=None, label: str=None, unit: str=None, is_rate: bool=False, is_discrete: bool=False, is_kpi: bool=False, is_impact: bool=False, is_key_attribute: bool=False, dashboard_order: int=None, data_type: str=None, is_property: bool=None):  # noqa: E501
        """AttributeDefinition - a model defined in Swagger

        :param key: The key of this AttributeDefinition.  # noqa: E501
        :type key: str
        :param label: The label of this AttributeDefinition.  # noqa: E501
        :type label: str
        :param unit: The unit of this AttributeDefinition.  # noqa: E501
        :type unit: str
        :param is_rate: The is_rate of this AttributeDefinition.  # noqa: E501
        :type is_rate: bool
        :param is_discrete: The is_discrete of this AttributeDefinition.  # noqa: E501
        :type is_discrete: bool
        :param is_kpi: The is_kpi of this AttributeDefinition.  # noqa: E501
        :type is_kpi: bool
        :param is_impact: The is_impact of this AttributeDefinition.  # noqa: E501
        :type is_impact: bool
        :param is_key_attribute: The is_key_attribute of this AttributeDefinition.  # noqa: E501
        :type is_key_attribute: bool
        :param dashboard_order: The dashboard_order of this AttributeDefinition.  # noqa: E501
        :type dashboard_order: int
        :param data_type: The data_type of this AttributeDefinition.  # noqa: E501
        :type data_type: str
        :param is_property: The is_property of this AttributeDefinition.  # noqa: E501
        :type is_property: bool
        """
        self.swagger_types = {
            'key': str,
            'label': str,
            'unit': str,
            'is_rate': bool,
            'is_discrete': bool,
            'is_kpi': bool,
            'is_impact': bool,
            'is_key_attribute': bool,
            'dashboard_order': int,
            'data_type': str,
            'is_property': bool
        }

        self.attribute_map = {
            'key': 'key',
            'label': 'label',
            'unit': 'unit',
            'is_rate': 'is_rate',
            'is_discrete': 'is_discrete',
            'is_kpi': 'is_kpi',
            'is_impact': 'is_impact',
            'is_key_attribute': 'is_key_attribute',
            'dashboard_order': 'dashboard_order',
            'data_type': 'data_type',
            'is_property': 'is_property'
        }
        self._key = key
        self._label = label
        self._unit = unit
        self._is_rate = is_rate
        self._is_discrete = is_discrete
        self._is_kpi = is_kpi
        self._is_impact = is_impact
        self._is_key_attribute = is_key_attribute
        self._dashboard_order = dashboard_order
        self._data_type = data_type
        self._is_property = is_property

    @classmethod
    def from_dict(cls, dikt) -> 'AttributeDefinition':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The AttributeDefinition of this AttributeDefinition.  # noqa: E501
        :rtype: AttributeDefinition
        """
        return util.deserialize_model(dikt, cls)

    @property
    def key(self) -> str:
        """Gets the key of this AttributeDefinition.


        :return: The key of this AttributeDefinition.
        :rtype: str
        """
        return self._key

    @key.setter
    def key(self, key: str):
        """Sets the key of this AttributeDefinition.


        :param key: The key of this AttributeDefinition.
        :type key: str
        """

        self._key = key

    @property
    def label(self) -> str:
        """Gets the label of this AttributeDefinition.


        :return: The label of this AttributeDefinition.
        :rtype: str
        """
        return self._label

    @label.setter
    def label(self, label: str):
        """Sets the label of this AttributeDefinition.


        :param label: The label of this AttributeDefinition.
        :type label: str
        """

        self._label = label

    @property
    def unit(self) -> str:
        """Gets the unit of this AttributeDefinition.


        :return: The unit of this AttributeDefinition.
        :rtype: str
        """
        return self._unit

    @unit.setter
    def unit(self, unit: str):
        """Sets the unit of this AttributeDefinition.


        :param unit: The unit of this AttributeDefinition.
        :type unit: str
        """

        self._unit = unit

    @property
    def is_rate(self) -> bool:
        """Gets the is_rate of this AttributeDefinition.


        :return: The is_rate of this AttributeDefinition.
        :rtype: bool
        """
        return self._is_rate

    @is_rate.setter
    def is_rate(self, is_rate: bool):
        """Sets the is_rate of this AttributeDefinition.


        :param is_rate: The is_rate of this AttributeDefinition.
        :type is_rate: bool
        """

        self._is_rate = is_rate

    @property
    def is_discrete(self) -> bool:
        """Gets the is_discrete of this AttributeDefinition.


        :return: The is_discrete of this AttributeDefinition.
        :rtype: bool
        """
        return self._is_discrete

    @is_discrete.setter
    def is_discrete(self, is_discrete: bool):
        """Sets the is_discrete of this AttributeDefinition.


        :param is_discrete: The is_discrete of this AttributeDefinition.
        :type is_discrete: bool
        """

        self._is_discrete = is_discrete

    @property
    def is_kpi(self) -> bool:
        """Gets the is_kpi of this AttributeDefinition.


        :return: The is_kpi of this AttributeDefinition.
        :rtype: bool
        """
        return self._is_kpi

    @is_kpi.setter
    def is_kpi(self, is_kpi: bool):
        """Sets the is_kpi of this AttributeDefinition.


        :param is_kpi: The is_kpi of this AttributeDefinition.
        :type is_kpi: bool
        """

        self._is_kpi = is_kpi

    @property
    def is_impact(self) -> bool:
        """Gets the is_impact of this AttributeDefinition.


        :return: The is_impact of this AttributeDefinition.
        :rtype: bool
        """
        return self._is_impact

    @is_impact.setter
    def is_impact(self, is_impact: bool):
        """Sets the is_impact of this AttributeDefinition.


        :param is_impact: The is_impact of this AttributeDefinition.
        :type is_impact: bool
        """

        self._is_impact = is_impact

    @property
    def is_key_attribute(self) -> bool:
        """Gets the is_key_attribute of this AttributeDefinition.


        :return: The is_key_attribute of this AttributeDefinition.
        :rtype: bool
        """
        return self._is_key_attribute

    @is_key_attribute.setter
    def is_key_attribute(self, is_key_attribute: bool):
        """Sets the is_key_attribute of this AttributeDefinition.


        :param is_key_attribute: The is_key_attribute of this AttributeDefinition.
        :type is_key_attribute: bool
        """

        self._is_key_attribute = is_key_attribute

    @property
    def dashboard_order(self) -> int:
        """Gets the dashboard_order of this AttributeDefinition.


        :return: The dashboard_order of this AttributeDefinition.
        :rtype: int
        """
        return self._dashboard_order

    @dashboard_order.setter
    def dashboard_order(self, dashboard_order: int):
        """Sets the dashboard_order of this AttributeDefinition.


        :param dashboard_order: The dashboard_order of this AttributeDefinition.
        :type dashboard_order: int
        """

        self._dashboard_order = dashboard_order

    @property
    def data_type(self) -> str:
        """Gets the data_type of this AttributeDefinition.


        :return: The data_type of this AttributeDefinition.
        :rtype: str
        """
        return self._data_type

    @data_type.setter
    def data_type(self, data_type: str):
        """Sets the data_type of this AttributeDefinition.


        :param data_type: The data_type of this AttributeDefinition.
        :type data_type: str
        """

        self._data_type = data_type

    @property
    def is_property(self) -> bool:
        """Gets the is_property of this AttributeDefinition.


        :return: The is_property of this AttributeDefinition.
        :rtype: bool
        """
        return self._is_property

    @is_property.setter
    def is_property(self, is_property: bool):
        """Sets the is_property of this AttributeDefinition.


        :param is_property: The is_property of this AttributeDefinition.
        :type is_property: bool
        """

        self._is_property = is_property