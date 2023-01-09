#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import functools
import time
from typing import Any
from typing import Callable
from typing import Tuple
from typing import Union


def timed(func: Callable) -> Callable:
    # Decorator used to time a function.
    # usage:
    #
    # @timed
    # def timed_function():
    #   [...]
    #
    # The function returns the elapsed time as a return value.
    # If the function returns no value, then elapsed time is returned as the sole return value
    # example: elapsed_time = timed_function()
    # If the function returns a tuple, then elapsed time is returned as the final item in the tuple
    # example: returned_tuple_1, returned_tuple_2, elapsed_time = timed_function()
    # Otherwise, return a tuple of the return value and elapsed time
    # example: returned_value, elapsed_time = timed_function()

    async def _process(func: Callable, *args: Any, **params: Any) -> Any:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **params)
        else:
            return func(*args, **params)

    @functools.wraps(func)
    async def timed_fn(*args: Any, **kwargs: Any) -> Union[float, Tuple]:
        start = time.perf_counter()

        value = await _process(func, *args, **kwargs)

        end = time.perf_counter()
        elapsed_time = end - start
        if value is None:
            return elapsed_time
        elif type(value) is tuple:
            return *value, elapsed_time
        else:
            return value, elapsed_time

    return timed_fn
