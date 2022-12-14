# coding: utf-8
#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import absolute_import

from datetime import date
from datetime import datetime
from typing import Dict
from typing import List

from swagger_server import util
from swagger_server.models.base_model_ import Model
from swagger_server.models.event import Event  # noqa: F401,E501
from swagger_server.models.metric_data import MetricData  # noqa: F401,E501
from swagger_server.models.object_key import ObjectKey  # noqa: F401,E501
from swagger_server.models.property_data import PropertyData  # noqa: F401,E501


class ObjectData(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(
        self,
        key: ObjectKey = None,
        metrics: List[MetricData] = None,
        properties: List[PropertyData] = None,
        events: List[Event] = None,
    ):  # noqa: E501
        """ObjectData - a model defined in Swagger

        :param key: The key of this ObjectData.  # noqa: E501
        :type key: ObjectKey
        :param metrics: The metrics of this ObjectData.  # noqa: E501
        :type metrics: List[MetricData]
        :param properties: The properties of this ObjectData.  # noqa: E501
        :type properties: List[PropertyData]
        :param events: The events of this ObjectData.  # noqa: E501
        :type events: List[Event]
        """
        self.swagger_types = {
            "key": ObjectKey,
            "metrics": List[MetricData],
            "properties": List[PropertyData],
            "events": List[Event],
        }

        self.attribute_map = {
            "key": "key",
            "metrics": "metrics",
            "properties": "properties",
            "events": "events",
        }
        self._key = key
        self._metrics = metrics
        self._properties = properties
        self._events = events

    @classmethod
    def from_dict(cls, dikt) -> "ObjectData":
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ObjectData of this ObjectData.  # noqa: E501
        :rtype: ObjectData
        """
        return util.deserialize_model(dikt, cls)

    @property
    def key(self) -> ObjectKey:
        """Gets the key of this ObjectData.


        :return: The key of this ObjectData.
        :rtype: ObjectKey
        """
        return self._key

    @key.setter
    def key(self, key: ObjectKey):
        """Sets the key of this ObjectData.


        :param key: The key of this ObjectData.
        :type key: ObjectKey
        """
        if key is None:
            raise ValueError(
                "Invalid value for `key`, must not be `None`"
            )  # noqa: E501

        self._key = key

    @property
    def metrics(self) -> List[MetricData]:
        """Gets the metrics of this ObjectData.

        Collection of metrics.  # noqa: E501

        :return: The metrics of this ObjectData.
        :rtype: List[MetricData]
        """
        return self._metrics

    @metrics.setter
    def metrics(self, metrics: List[MetricData]):
        """Sets the metrics of this ObjectData.

        Collection of metrics.  # noqa: E501

        :param metrics: The metrics of this ObjectData.
        :type metrics: List[MetricData]
        """

        self._metrics = metrics

    @property
    def properties(self) -> List[PropertyData]:
        """Gets the properties of this ObjectData.

        Collection of properties.  # noqa: E501

        :return: The properties of this ObjectData.
        :rtype: List[PropertyData]
        """
        return self._properties

    @properties.setter
    def properties(self, properties: List[PropertyData]):
        """Sets the properties of this ObjectData.

        Collection of properties.  # noqa: E501

        :param properties: The properties of this ObjectData.
        :type properties: List[PropertyData]
        """

        self._properties = properties

    @property
    def events(self) -> List[Event]:
        """Gets the events of this ObjectData.


        :return: The events of this ObjectData.
        :rtype: List[Event]
        """
        return self._events

    @events.setter
    def events(self, events: List[Event]):
        """Sets the events of this ObjectData.


        :param events: The events of this ObjectData.
        :type events: List[Event]
        """

        self._events = events
