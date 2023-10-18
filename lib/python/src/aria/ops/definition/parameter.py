#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from abc import ABC
from typing import Optional
from typing import Union

from aria.ops.definition.assertions import validate_key
from aria.ops.definition.exceptions import DuplicateKeyException


class Parameter(ABC):
    def __init__(
        self,
        key: str,
        label: Optional[str] = None,
        description: Optional[str] = None,
        default: Optional[Union[str, int]] = None,
        required: bool = True,
        advanced: bool = False,
        display_order: int = 0,
    ) -> None:
        """
        Args:
            key (str): Used to identify the parameter.
            label (Optional[str]): Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
            description (Optional[str]): More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
            default (Optional[Union[str, int]]): The default value of the parameter.
            required (bool): True if user is required to provide this parameter. Defaults to True.
            advanced (bool): True if the parameter should be collapsed by default. Defaults to False.
            display_order (int): Determines the order parameters will be displayed in the UI.
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

    def to_json(self) -> dict:
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
    def __init__(
        self,
        key: str,
        label: Optional[str] = None,
        description: Optional[str] = None,
        default: Optional[int] = None,
        required: bool = True,
        advanced: bool = False,
        display_order: int = 0,
    ) -> None:
        """

        Args:
            key (str): Used to identify the parameter.
            label (Optional[str]): Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
            description (Optional[str]): More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
            default (Optional[int]): The default value of the parameter.
            required (bool): True if user is required to provide this parameter. Defaults to True.
            advanced (bool): True if the parameter should be collapsed by default. Defaults to False.
            display_order (int): Determines the order parameters will be displayed in the UI.
        """
        super().__init__(
            key, label, description, default, required, advanced, display_order
        )

    def to_json(self) -> dict:
        return super().to_json() | {
            "type": "integer",
            "default": str(self.default) if self.default is not None else None,
        }


class StringParameter(Parameter):
    def __init__(
        self,
        key: str,
        label: Optional[str] = None,
        description: Optional[str] = None,
        default: Optional[str] = None,
        max_length: int = 512,
        required: bool = True,
        advanced: bool = False,
        display_order: int = 0,
    ) -> None:
        """
        Args:
           key (str): Used to identify the parameter.
           label (Optional[str]): Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
           description (Optional[str]): More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
           default (Optional[str]): The default value of the parameter.
           max_length (int): The max length of the parameter value. Defaults to 512.
           required (bool): True if user is required to provide this parameter. Defaults to True.
           advanced (bool): True if the parameter should be collapsed by default. Defaults to False.
           display_order (int): Determines the order parameters will be displayed in the UI.
        """
        super().__init__(
            key, label, description, default, required, advanced, display_order
        )
        self.max_length = max_length

    def to_json(self) -> dict:
        return super().to_json() | {
            "type": "string",
            "length": int(self.max_length),
            "default": self.default,
        }


class EnumParameter(Parameter):
    def __init__(
        self,
        key: str,
        values: list[Union[str, tuple[str, str]]],
        label: Optional[str] = None,
        description: Optional[str] = None,
        default: Optional[str] = None,
        required: bool = True,
        advanced: bool = False,
        display_order: int = 0,
    ) -> None:
        """

        Args:
            key (str): Used to identify the parameter.
            values (list[Union[str, tuple[str, str]]]): An array containing all enum values. If 'default' is specified
                and not part of this array, it will be added as an additional enum value. Enum values are not
                localizable.
            label (Optional[str]): Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
            description (Optional[str]): More in-depth explanation of the parameter. Displayed as a tooltip in the
                VMware Aria Operations UI.
            default (Optional[str]): The default value of the parameter.
            required (bool): True if user is required to provide this parameter. Defaults to True.
            advanced (bool): True if the parameter should be collapsed by default. Defaults to False.
            display_order (int): Determines the order parameters will be displayed in the UI.
        """
        super().__init__(
            key, label, description, default, required, advanced, display_order
        )
        if len(values) > len(set(values)):
            raise DuplicateKeyException(
                f"Duplicate enum value in parameter {key}: {values}."
            )

        self.values = values
        self.default = default

        if (
            default not in [v[0] if isinstance(v, tuple) else v for v in self.values]
            and default is not None
        ):
            self.values.append((default, default))

    def to_json(self) -> dict:
        return super().to_json() | {
            "type": "string",
            "enum": True,
            "enum_values": [
                {
                    "key": str(value[0]) if isinstance(value, tuple) else value,
                    "label": str(value[1]) if isinstance(value, tuple) else value,
                    "display_order": display_order,
                }
                for display_order, value in enumerate(self.values)
            ],
            "default": self.default,
        }
