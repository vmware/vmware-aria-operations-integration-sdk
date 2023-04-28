#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from abc import ABC
from collections import OrderedDict
from typing import Optional
from typing import Union

from aria.ops.definition.assertions import validate_key
from aria.ops.definition.exceptions import DuplicateKeyException


class CredentialParameter(ABC):
    def __init__(
        self,
        key: str,
        label: Optional[str] = None,
        required: bool = True,
        display_order: int = 0,
    ):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param display_order: Determines the order parameters will be displayed in the UI.
        """
        self.key = validate_key(key, "Credential parameter")
        self.label = label
        if label is None:
            self.label = key
        self.required = required
        self.display_order = display_order

    def to_json(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "required": self.required,
            "password": False,
            "enum": False,
            "display_order": self.display_order,
        }


class CredentialIntParameter(CredentialParameter):
    """
    :param key: Used to identify the parameter.
    :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
    :param required: True if user is required to provide this parameter. Defaults to True.
    :param display_order: Determines the order parameters will be displayed in the UI.
    """

    def __init__(
        self,
        key: str,
        label: Optional[str] = None,
        required: bool = True,
        display_order: int = 0,
    ):
        super().__init__(key, label, required, display_order)

    def to_json(self) -> dict:
        return super().to_json() | {
            "type": "integer",
        }


class CredentialStringParameter(CredentialParameter):
    def __init__(
        self,
        key: str,
        label: Optional[str] = None,
        required: bool = True,
        display_order: int = 0,
    ):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param display_order: Determines the order parameters will be displayed in the UI.
        """
        super().__init__(key, label, required, display_order)

    def to_json(self) -> dict:
        return super().to_json() | {
            "type": "string",
        }


class CredentialPasswordParameter(CredentialParameter):
    def __init__(
        self,
        key: str,
        label: Optional[str] = None,
        required: bool = True,
        display_order: int = 0,
    ):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param display_order: Determines the order parameters will be displayed in the UI.
        """
        super().__init__(key, label, required, display_order)

    def to_json(self) -> dict:
        return super().to_json() | {
            "type": "string",
            "password": True,
        }


class CredentialEnumParameter(CredentialParameter):
    """
    :param key: Used to identify the parameter.
    :param values: An array containing all enum values. If 'default' is specified and not part of this array, it
           will be added as an additional enum value. Enum values are not localizable.
    :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
    :param default: The default value of the enum.
    :param required: True if user is required to provide this parameter. Defaults to True.
    :param display_order: Determines the order parameters will be displayed in the UI.
    """

    def __init__(
        self,
        key: str,
        values: list[Union[str, tuple[str, str]]],
        label: Optional[str] = None,
        default: Optional[str] = None,
        required: bool = True,
        display_order: int = 0,
    ):
        super().__init__(key, label, required, display_order)
        self.values = values

        if (
            default not in [v[0] if isinstance(v, tuple) else v for v in self.values]
            and default is not None
        ):
            self.values.append((default, default))

        # set the default value to the value of the label if they are diferent, otherwise set to the passed default
        self.default = next(
            (v[1] for v in self.values if isinstance(v, tuple) and v[0] == default),
            default,
        )

    def to_json(self) -> dict:
        return super().to_json() | {
            "type": "string",
            "default": self.default,
            "enum": True,
            "enum_values": [
                {
                    "key": str(value[0]) if isinstance(value, tuple) else value,
                    "label": str(value[1]) if isinstance(value, tuple) else value,
                    "display_order": display_order,
                }
                for display_order, value in enumerate(self.values)
            ],
        }


class CredentialType:
    def __init__(self, key: str, label: Optional[str] = None):
        self.key = validate_key(key, "Credential type")
        self.label = label
        if label is None:
            self.label = key
        self.credential_parameters: dict = OrderedDict()

    def define_string_parameter(
        self, key: str, label: Optional[str] = None, required: bool = True
    ) -> CredentialStringParameter:
        """
        Create a new string credential parameter and apply it to this credential definition.
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :return The created string parameter definition.
        """
        field = CredentialStringParameter(key, label, required)
        self.add_parameter(field)
        return field

    def define_int_parameter(
        self, key: str, label: Optional[str] = None, required: bool = True
    ) -> CredentialIntParameter:
        """
        Create a new int credential parameter and apply it to this credential definition.
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :return The created int parameter definition.
        """
        field = CredentialIntParameter(key, label, required)
        self.add_parameter(field)
        return field

    def define_password_parameter(
        self, key: str, label: Optional[str] = None, required: bool = True
    ) -> CredentialPasswordParameter:
        """
        Create a new password credential parameter and apply it to this credential definition.
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :return The created password parameter definition.
        """
        field = CredentialPasswordParameter(key, label, required)
        self.add_parameter(field)
        return field

    def define_enum_parameter(
        self,
        key: str,
        values: list[Union[str, tuple[str, str]]],
        label: Optional[str] = None,
        default: Optional[str] = None,
        required: bool = True,
    ) -> CredentialEnumParameter:
        """
        Create a new enum credential parameter and apply it to this credential definition.
        :param key: Used to identify the parameter.
        :param values: An array containing all enum values. If 'default' is specified and not part of this array, it
               will be added as an additional enum value. Enum values are not localizable.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param default: The default value of the enum.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :return The created enum parameter definition.
        """
        field = CredentialEnumParameter(key, values, label, default, required)
        self.add_parameter(field)
        return field

    def add_parameters(self, credential_parameters: list[CredentialParameter]) -> None:
        """
        :param credential_parameters: A list of parameters to add to the credential
        :return None
        """
        for credential_parameter in credential_parameters:
            self.add_parameter(credential_parameter)

    def add_parameter(self, credential_parameter: CredentialParameter) -> None:
        """
        :param credential_parameter: The parameter to add to the credential
        :return None
        """
        key = credential_parameter.key
        if key in self.credential_parameters:
            raise DuplicateKeyException(
                f"Credential field with key {key} already exists in adapter definition."
            )
        credential_parameter.display_order = len(self.credential_parameters)
        self.credential_parameters[key] = credential_parameter

    def to_json(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "fields": [
                field.to_json() for field in self.credential_parameters.values()
            ],
        }
