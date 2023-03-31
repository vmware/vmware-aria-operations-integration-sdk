#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from enum import Enum
from typing import List
from typing import Tuple


class ResultLevel(Enum):
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    SUCCESS = 4


class Result:
    def __init__(self) -> None:
        self.messages: List[Tuple[ResultLevel, str]] = []
        self.warning_count: int = 0
        self.error_count: int = 0

    def __iadd__(self, other: Result) -> Result:
        self.error_count = self.error_count + other.error_count
        self.warning_count = self.warning_count + other.warning_count
        self.messages = self.messages + other.messages
        return self

    def issue_count(self) -> int:
        return self.error_count + self.warning_count

    def with_error(self, error: str) -> None:
        self.error_count += 1
        self.messages.append((ResultLevel.ERROR, error))

    def with_warning(self, warning: str) -> None:
        self.warning_count += 1
        self.messages.append((ResultLevel.WARNING, warning))

    def with_information(self, information: str) -> None:
        self.messages.append((ResultLevel.INFORMATION, information))

    def with_success(self, success: str) -> None:
        self.messages.append((ResultLevel.SUCCESS, success))
