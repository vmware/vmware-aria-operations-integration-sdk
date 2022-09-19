#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

_DEFAULT_THREAD_POOL = ThreadPoolExecutor()


def threaded(function, executor=None):
    @wraps(function)
    def threaded_function(*args, **kwargs):
        return (executor or _DEFAULT_THREAD_POOL).submit(function, *args, **kwargs)

    return threaded_function
