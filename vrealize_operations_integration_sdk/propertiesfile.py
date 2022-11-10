
#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

def load_properties(properties_file: str):
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


def write_properties(properties: dict, filename: str):
    with open(filename, "w") as f:
        for _property in properties.keys():
            f.write(str(_property) + " = " + str(properties[_property]) + "\n")
    return True
