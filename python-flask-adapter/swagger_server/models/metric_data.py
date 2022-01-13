# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class MetricData(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    def __init__(self, key: str=None, number_value: float=None, timestamp: int=-1):  # noqa: E501
        """MetricData - a model defined in Swagger

        :param key: The key of this MetricData.  # noqa: E501
        :type key: str
        :param number_value: The number_value of this MetricData.  # noqa: E501
        :type number_value: float
        :param timestamp: The timestamp of this MetricData.  # noqa: E501
        :type timestamp: int
        """
        self.swagger_types = {
            'key': str,
            'number_value': float,
            'timestamp': int
        }

        self.attribute_map = {
            'key': 'key',
            'number_value': 'numberValue',
            'timestamp': 'timestamp'
        }
        self._key = key
        self._number_value = number_value
        self._timestamp = timestamp

    @classmethod
    def from_dict(cls, dikt) -> 'MetricData':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The MetricData of this MetricData.  # noqa: E501
        :rtype: MetricData
        """
        return util.deserialize_model(dikt, cls)

    @property
    def key(self) -> str:
        """Gets the key of this MetricData.

        Key represents a hierarchical structure for an individual metric. The formation of the metric key is an important part of designing a data feed. Well formed metric keys will lead to better usability, performance and visualization of analytics results, such as root cause analysis.  The base concepts are as follows:<br> A metric key can consist of any number of hierarchical groups. Each hierarchical group can contain instances. The last item in the hierarchy is assumed to be the name of the metric. The hierarchy without instance names represents an attribute that can be collected. If there are no instances, then a metric key and an attribute are one and the same.  # noqa: E501

        :return: The key of this MetricData.
        :rtype: str
        """
        return self._key

    @key.setter
    def key(self, key: str):
        """Sets the key of this MetricData.

        Key represents a hierarchical structure for an individual metric. The formation of the metric key is an important part of designing a data feed. Well formed metric keys will lead to better usability, performance and visualization of analytics results, such as root cause analysis.  The base concepts are as follows:<br> A metric key can consist of any number of hierarchical groups. Each hierarchical group can contain instances. The last item in the hierarchy is assumed to be the name of the metric. The hierarchy without instance names represents an attribute that can be collected. If there are no instances, then a metric key and an attribute are one and the same.  # noqa: E501

        :param key: The key of this MetricData.
        :type key: str
        """
        if key is None:
            raise ValueError("Invalid value for `key`, must not be `None`")  # noqa: E501

        self._key = key

    @property
    def number_value(self) -> float:
        """Gets the number_value of this MetricData.

        Current double value.  # noqa: E501

        :return: The number_value of this MetricData.
        :rtype: float
        """
        return self._number_value

    @number_value.setter
    def number_value(self, number_value: float):
        """Sets the number_value of this MetricData.

        Current double value.  # noqa: E501

        :param number_value: The number_value of this MetricData.
        :type number_value: float
        """

        self._number_value = number_value

    @property
    def timestamp(self) -> int:
        """Gets the timestamp of this MetricData.

        Timestamp of the data.  # noqa: E501

        :return: The timestamp of this MetricData.
        :rtype: int
        """
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp: int):
        """Sets the timestamp of this MetricData.

        Timestamp of the data.  # noqa: E501

        :param timestamp: The timestamp of this MetricData.
        :type timestamp: int
        """

        self._timestamp = timestamp
