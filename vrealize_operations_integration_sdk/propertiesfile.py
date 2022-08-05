
#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

def load_properties(properties_file):
    properties = {}
    try:
        with open(properties_file, "r") as f:
            for line in f:
                l = line.strip()
                if l and not l.startswith("#"):
                    (key, _, value) = l.partition("=")
                    if value.strip():
                        properties[key.strip()] = value.strip()
    except FileNotFoundError as e:
        # resources.properties file is not required to exist
        pass
    return properties
