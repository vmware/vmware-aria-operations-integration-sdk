#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from aria.ops.definition.exceptions import KeyException


def validate_key(key: str, context: str) -> str:
    if key is None:
        raise KeyException(f"{context} key cannot be 'None'.")
    if type(key) is not str:
        raise KeyException(f"{context} key must be a string.")
    if key == "":
        raise KeyException(f"{context} key cannot be empty.")
    if key.isspace():
        raise KeyException(f"{context} key cannot be blank.")
    return key
