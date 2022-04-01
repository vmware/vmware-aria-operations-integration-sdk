__author__ = 'VMware, Inc.'
__copyright__ = 'Copyright 2022 VMware, Inc. All rights reserved.'

import time


class Metric:
    def __init__(self, key: str, value: float, timestamp: int = int(time.time() * 1000)):
        self.key = key
        self.value = value
        self.timestamp = timestamp

    def get_json(self):
        return {
            "key": self.key,
            "numberValue": float(self.value),
            "timestamp": self.timestamp
        }


class Property:
    def __init__(self, key: str, value, timestamp: int = int(time.time() * 1000)):
        self.key = key
        self.value = value
        self.timestamp = timestamp

    def get_json(self):
        if isinstance(self.value, str):
            label = "stringValue"
        else:
            label = "numberValue"
            self.value = float(self.value)

        return {
            "key": self.key,
            label: self.value,
            "timestamp": self.timestamp
        }
