#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from abc import ABC

from vrops.definition.assertions import validate_key


class Parameter(ABC):
    def __init__(self,
                 key: str,
                 label: str = None,
                 description: str = None,
                 default: str | int = None,
                 required: bool = True,
                 advanced: bool = False,
                 display_order: int = 0):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
        :param default: The default value of the parameter.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :param display_order: Determines the order parameters will be displayed in the UI.
        """
        self.key = validate_key(key, "Parameter/Identifier")
        self.label = label
        if label is None:
            self.label = key
        self.description = description
        self.default = default
        self.required = required
        self.advanced = advanced
        self.display_order = display_order

    def to_json(self):
        return {
            "key": self.key,
            "label": self.label,
            "description": self.description,
            "required": self.required,
            "ident_type": 1 if not self.advanced else 2,
            "enum": False,
            "display_order": self.display_order,
        }


class IntParameter(Parameter):
    def __init__(self, key: str, label: str = None, description: str = None, default: int = None, required: bool = True,
                 advanced: bool = False, display_order: int = 0):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
        :param default: The default value of the parameter.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :param display_order: Determines the order parameters will be displayed in the UI.
        """
        super().__init__(key, label, description, default, required, advanced, display_order)

    def to_json(self):
        return super().to_json() | {
            "type": "integer",
            "default": int(self.default),
        }


class StringParameter(Parameter):
    def __init__(self, key: str, label: str = None, description: str = None, default: str = None,
                 max_length: int = None, required: bool = True, advanced: bool = False, display_order: int = 0):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
        :param default: The default value of the parameter.
        :param max_length: The max length of the parameter value.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :param display_order: Determines the order parameters will be displayed in the UI.
        """
        super().__init__(key, label, description, default, required, advanced, display_order)
        self.max_length = max_length

    def to_json(self):
        return super().to_json() | {
            "type": "string",
            "length": self.max_length,
            "default": str(self.default)
        }


class EnumParameter(Parameter):
    def __init__(self, key: str, values: list[str], label: str = None, description: str = None,
                 default: str = None, required: bool = True, advanced: bool = False, display_order: int = 0):
        """
        :param key: Used to identify the parameter.
        :param values: An array containing all enum values. If 'default' is specified and not part of this array, it
               will be added as an additional enum value. Enum values are not localizable.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
        :param default: The default value of the parameter.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :param display_order: Determines the order parameters will be displayed in the UI.
        """
        super().__init__(key, label, description, default, required, advanced, display_order)
        self.values = list(set(values))
        if default not in self.values:
            self.values.append(default)

    def to_json(self):
        return super().to_json() | {
            "type": "string",
            "enum": True,
            "enum_values": [str(value) for value in self.values]
        }
