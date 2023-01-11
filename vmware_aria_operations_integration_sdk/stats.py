#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from statistics import median
from statistics import stdev
from typing import List
from typing import Set


def convert_bytes(bytes: int) -> str:
    tags = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]

    i = 0
    double_bytes = float(bytes)

    while i < len(tags) and double_bytes >= 1024:
        double_bytes = double_bytes / 1024.0
        i = i + 1

    return str(round(double_bytes, 2)) + " " + tags[i]


class Stats:
    def __init__(self, array: List, unit: str = "") -> None:
        self.data_points = len(array)
        self.count = sum(array)
        self.median = median(array)
        self.min = min(array)
        self.max = max(array)
        self.stddev = float("NaN")
        self.unit = unit
        if len(array) > 2:
            self.stddev = stdev(array)

    def __repr__(self) -> str:
        if self.data_points <= 1 or self.count == 0:
            return f"{self.count} {self.unit}"
        else:
            return f"{self.count} {self.unit}({self.min} {self.unit}/{self.median} {self.unit}/{self.max} {self.unit})"


class LongRunStats(Stats):
    def __init__(self, array: List[float], unit: str = "") -> None:
        super().__init__(array, unit)
        self.average = get_average(array)

    def __repr__(self) -> str:
        if self.data_points <= 1 or self.count == 0:
            return f"{self.average:.1f} {self.unit}"
        else:
            return f"{self.average:.1f} {self.unit} ({self.min:.1f}{self.unit} / {self.median:.1f}{self.unit} / {self.max:.1f}{self.unit})"


def get_average(inputs: List[float]) -> float:
    return sum(inputs) / len(inputs)


def get_growth_rate(initial: float, final: float, duration: float) -> float:
    """
    Calculates average percent growth rate per period
    :param initial: the initial number of objects / things
    :param final: the final number of objects / things
    :param duration: the total time period in any given unit
    :return: float that represents the percent of growth per period unit
    """
    # Adding one to the formula allows us to account for cases where zero is the initial or final value
    if not (final > 0 and initial > 0):
        initial += 1
        final += 1

    assert initial >= 0
    assert final >= 0
    assert final >= initial

    return float(((final / initial) ** (1 / duration)) - 1) * 100


class UniqueObjectTypeStatistics:
    def __init__(self) -> None:
        self.running_collection: Set = set()
        self.data_points: List = list()
        self.counts: List = list()

    def add(self, unique_items: Set, total_items: int) -> None:
        self.running_collection.update(unique_items)
        self.data_points.append(len(self.running_collection))
        self.counts.append(total_items)
