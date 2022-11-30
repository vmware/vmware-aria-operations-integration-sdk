#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import time
from typing import Union


class Metric:
    """Class representing a Metric Data Point.

    Metrics are numeric values that represent data at a particular point in time. These are stored as time series data.
    Examples:
        CPU Utilization
        Disk Capacity
        Current User Session Count
        Cumulative Data Received
    """

    def __init__(self, key: str, value: float, timestamp: int = None):
        """Creates a Metric

        :param key: A string representing the type of metric. TODO: Describe how Keys work.
        :param value: The value of the Metric. Must be type float.
        :param timestamp: Time in milliseconds since the Epoch when this metric value was recorded.
            Defaults to the current time.
        """
        self.key = key
        self.value = value

        if timestamp is None:
            self.timestamp = int(time.time() * 1000)
        else:
            self.timestamp = timestamp

    def get_json(self):
        """Get a JSON representation of this Metric.

        Returns a JSON representation of this Metric in the format required by vROps.

        :return: A JSON representation of this Metric.
        """
        return {
            "key": self.key,
            "numberValue": float(self.value),
            "timestamp": self.timestamp,
        }


class Property:
    """Class representing a Property value.

    A Property is a value, usually a string, that will change infrequently or not at all. Only the current value is
    important.
    Examples:
        IP Address
        Software Version
        CPU Core Count
    """

    def __init__(self, key: str, value: Union[float, str], timestamp: int = None):
        """Creates a Property.

        :param key: A string representing the type of property. TODO: Describe how Keys work.
        :param value: The value of the property. Can be str or float.
        :param timestamp: Time in milliseconds since the Epoch when this property value was recorded.
            Defaults to the current time.
        """
        self.key = key
        self.value = value

        if timestamp is None:
            self.timestamp = int(time.time() * 1000)
        else:
            self.timestamp = timestamp

    def get_json(self):
        """Get a JSON representation of this Property.

        Returns a JSON representation of this Property in the format required by vROps.

        :return: A JSON representation of this Property.
        """
        if isinstance(self.value, str):
            label = "stringValue"
        else:
            label = "numberValue"
            self.value = float(self.value)

        return {"key": self.key, label: self.value, "timestamp": self.timestamp}
