#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import time
from typing import Optional
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

    def __init__(self, key: str, value: float, timestamp: Optional[int] = None):
        """
        Creates a Metric.

        Args:
            key (str): A string representing the type of metric.
            value (float): The value of the Metric.
            timestamp (Optional[int], optional): Time in milliseconds since the Epoch when this metric
                                                 value was recorded. Defaults to the current time.
        """
        self.key = key
        self.value = value

        if timestamp is None:
            self.timestamp = int(time.time() * 1000)
        else:
            self.timestamp = timestamp

    def get_json(self) -> dict:
        """
        Get a JSON representation of this Metric.

        Returns a JSON representation of this Metric in the format required by vROps.

        Returns:
            dict: A JSON representation of this Metric.
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

    def __init__(
        self, key: str, value: Union[float, str], timestamp: Optional[int] = None
    ):
        """
        Creates a Property.

        Args:
            key (str): A string representing the type of property.
            value (Union[float, str]): The value of the property. Can be str or float.
            timestamp (Optional[int], optional): Time in milliseconds since the Epoch when this property
                                                 value was recorded. Defaults to the current time.
        """
        self.key = key
        self.value = value

        if timestamp is None:
            self.timestamp = int(time.time() * 1000)
        else:
            self.timestamp = timestamp

    def get_json(self) -> dict:
        """
        Get a JSON representation of this Property.

        Returns a JSON representation of this Property in the format required by vROps.

        Returns:
            dict: A JSON representation of this Property.
        """
        if isinstance(self.value, str):
            label = "stringValue"
        else:
            label = "numberValue"
            self.value = float(self.value)

        return {"key": self.key, label: self.value, "timestamp": self.timestamp}
