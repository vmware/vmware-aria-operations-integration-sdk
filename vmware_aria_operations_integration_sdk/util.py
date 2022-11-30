#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0


class LazyAttribute(object):
    def __init__(self, computation_function):
        self.computation_function = computation_function
        self.attribute_name = computation_function.__name__

    def __get__(self, instance, owner):
        if self.attribute_name not in instance.__dict__:
            instance.__dict__[self.attribute_name] = self.computation_function(instance)

        return instance.__dict__[self.attribute_name]
