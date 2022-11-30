#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from enum import Enum


class ResultLevel(Enum):
    ERROR = 1
    WARNING = 2
    INFORMATION = 3


class Result:
    def __init__(self):
        self.messages: list[(ResultLevel, str)] = []
        self.warning_count: int = 0
        self.error_count: int = 0

    def __iadd__(self, other):
        self.error_count = self.error_count + other.error_count
        self.warning_count = self.warning_count + other.warning_count
        self.messages = self.messages + other.messages
        return self

    def with_error(self, error):
        self.error_count += 1
        self.messages.append((ResultLevel.ERROR, error))

    def with_warning(self, warning):
        self.warning_count += 1
        self.messages.append((ResultLevel.WARNING, warning))

    def with_information(self, information):
        self.messages.append((ResultLevel.INFORMATION, information))
