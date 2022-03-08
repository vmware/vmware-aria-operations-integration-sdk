import json
import os

import common.constant as constant

from common.filesystem import get_absolute_project_directory


# Given a config key, return the value associated with it, or if no value exists,
# return the default value if provided. If no value exists and a default is not provided,
# this function prompts the user for a value. If the value changed, the new value is
# stored back into the config file.
def get_config_value(key: str, default: any = None, config_file: str = "config.json") -> object:
    defaults = {key: default}
    if default is None:
        defaults = None
    return get_config_values(key, defaults=defaults, config_file=config_file)[key]


# Given a list of config keys, return a dictionary of keys and the values associated with them
# If no value exists for a given key, return the default value if provided. If no value exists
# and a default is not provided, this function prompts the user for a value. If a value
# changed, the new value is stored back into the config file.
# TODO: Improve handling of user input
# TODO: Password values should be encrypted in the file and obscured when asking for input
def get_config_values(*keys: [str], defaults: dict[str, any] = None, config_file: str = constant.CONFIG_FILE):
    if defaults is None:
        defaults = {}
    config_file_path = get_absolute_project_directory(config_file)

    if not os.path.isfile(config_file_path):
        with open(config_file_path, "w") as config:
            json.dump({}, config, indent=4, sort_keys=True)

    with open(config_file_path, "r") as config:
        config_json = json.load(config)

        values = {}

        for key in keys:
            if key in config_json:
                values[key] = config_json[key]
            elif key in defaults:
                values[key] = defaults[key]
                config_json[key] = defaults[key]
            else:
                values[key] = input(f"{key}: ")
                config_json[key] = values[key]

    with open(config_file_path, "w") as config:
        json.dump(config_json, config, indent=4, sort_keys=True)

    return values


# Given a key and a value, write the given value to key 'key'. If the key does not exist it will
# be created. If the key does exist, the value will be overwritten with the contents of 'value'
def set_config_value(key: str, value: any, config_file: str = constant.CONFIG_FILE):
    config_file_path = get_absolute_project_directory(config_file)

    if not os.path.isfile(config_file_path):
        with open(config_file_path, "w") as config:
            json.dump({}, config, indent=4, sort_keys=True)

    with open(config_file_path, "r") as config:
        config_json = json.load(config)

        config_json[key] = value

    with open(config_file_path, "w") as config:
        json.dump(config_json, config, indent=4, sort_keys=True)
