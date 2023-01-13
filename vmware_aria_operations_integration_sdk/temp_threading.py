#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from concurrent.futures import Executor
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any
from typing import Callable
from typing import Optional

_DEFAULT_THREAD_POOL = ThreadPoolExecutor()


def threaded(function: Callable, executor: Optional[Executor] = None) -> Callable:
    @wraps(function)
    def threaded_function(*args: Any, **kwargs: Any) -> Future:
        return (executor or _DEFAULT_THREAD_POOL).submit(function, *args, **kwargs)

    return threaded_function
