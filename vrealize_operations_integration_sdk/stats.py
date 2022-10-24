#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0


from statistics import median, stdev


def convert_bytes(bytes_number):
    tags = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]

    i = 0
    double_bytes = bytes_number

    while i < len(tags) and bytes_number >= 1024:
        double_bytes = bytes_number / 1024.0
        i = i + 1
        bytes_number = bytes_number / 1024

    return str(round(double_bytes, 2)) + " " + tags[i]


class Stats:
    def __init__(self, array, unit=""):
        self.data_points = len(array)
        self.count = sum(array)
        self.median = median(array)
        self.min = min(array)
        self.max = max(array)
        self.stddev = float("NaN")
        self.unit = unit
        if len(array) > 2:
            self.stddev = stdev(array)

    def __repr__(self):
        if self.data_points <= 1 or self.count == 0:
            return f"{self.count} {self.unit}"
        else:
            return f"{self.count} {self.unit}({self.min} {self.unit}/{self.median} {self.unit}/{self.max} {self.unit})"


class LongRunStats(Stats):
    def __init__(self, array, unit=""):
        super().__init__(array, unit)
        self.average = get_average(array)

    def __repr__(self):
        if self.data_points <= 1 or self.count == 0:
            return f"{self.average:.1f} {self.unit}"
        else:
            return f"{self.average:.1f} {self.unit} ({self.min:.1f}{self.unit} / {self.median:.1f}{self.unit} / {self.max:.1f}{self.unit})"


def get_average(inputs: list):
    return sum(inputs) / len(inputs)


# TODO: change signature to initial, final, and time
def get_growth_rate(initial, final, size):
    # Adding one to the formula allows us to account for cases where zero is the initial or final value
    if not (final and initial):
        initial += 1
        final += 1

    return (((final / initial) ** (1 / size)) - 1) * 100


class UniqueObjectTypeStatistics:
    def __init__(self):
        self.running_collection = set()
        self.data_points = list()
        self.counts = list()

    def add(self, unique_items, total_items):
        self.running_collection.update(unique_items)
        self.data_points.append(len(self.running_collection))
        self.counts.append(total_items)
