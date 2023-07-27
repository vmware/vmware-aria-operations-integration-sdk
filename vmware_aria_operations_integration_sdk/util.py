#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import argparse
from typing import Any
from typing import Callable
from typing import Optional


class LazyAttribute(object):
    def __init__(self, computation_function: Callable) -> None:
        self.computation_function = computation_function
        self.attribute_name = computation_function.__name__

    def __get__(self, instance: Optional[object], owner: Optional[type[object]]) -> Any:
        if not instance:
            raise AttributeError("LazyAttribute 'get' cannot be called on a class.")
        if self.attribute_name not in instance.__dict__:
            instance.__dict__[self.attribute_name] = self.computation_function(instance)

        return instance.__dict__[self.attribute_name]


def port_range(port: str) -> int:
    try:
        val = int(port)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer value: {port}")

    if 0 > val or val > 2**16:
        raise argparse.ArgumentTypeError(f"port should be between 0 and {2 ** 16}")
    else:
        return val


def verbosity_range(verbosity_level: str) -> int:
    try:
        val = int(verbosity_level)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer value: {verbosity_level}")

    if 0 > val or val > 3:
        raise argparse.ArgumentTypeError(f"Verbosity should be between 0 and 3")
    else:
        return val
