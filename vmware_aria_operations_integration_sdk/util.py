#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import argparse
from typing import Any
from typing import Callable
from typing import Optional
from typing import Union


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


class RangeAction(argparse.Action):
    def __init__(
        self,
        option_strings: list[str],
        dest: str,
        lower_bound: int = 0,
        upper_bound: int = 100,
        **kwargs: Any,
    ):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        print(f"TYPE: {type(kwargs)}")

        if "metavar" not in kwargs:
            kwargs.setdefault("metavar", f"[{lower_bound}-{upper_bound}]")

        super(RangeAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: Optional[str] = None,
    ) -> None:
        try:
            value = int(values)
        except ValueError:
            raise argparse.ArgumentError(self, f"Invalid integer value: {values}")

        if not self.lower_bound <= value <= self.upper_bound:
            raise argparse.ArgumentError(
                self,
                f"Value must be an integer between {self.lower_bound} and {self.upper_bound}.",
            )

        setattr(namespace, self.dest, value)
