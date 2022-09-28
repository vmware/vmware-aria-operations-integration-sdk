#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from abc import ABC


class CredentialParameter(ABC):
    def __init__(self, key: str, label: str = None, credential_type: str = "default_credential", required: bool = True, display_order: int = 0):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param credential_type: A group of credential parameters comprises a credential type. An adapter can have multiple types of credentials, which the user can choose between when creating an adapter instance. The default type is 'default_credential', which is useful for the common case where only one credential type is required.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param display_order: Determines the order parameters will be displayed in the UI.
        """
        self.key = key
        self.label = label
        self.credential_type = credential_type
        self.required = required
        self.display_order = display_order

    def to_json(self):
        return {
            "key": self.key,
            "label": self.label,
            "required": self.required,
            "password": False,
            "enum": False,
            "display_order": self.display_order
        }


class IntCredentialParameter(CredentialParameter):
    """
    :param key: Used to identify the parameter.
    :param label: Label that is displayed in the vROps UI. Defaults to the key.
    :param credential_type: A group of credential parameters comprises a credential type. An adapter can have multiple types of credentials, which the user can choose between when creating an adapter instance. The default type is 'default_credential', which is useful for the common case where only one credential type is required.
    :param required: True if user is required to provide this parameter. Defaults to True.
    :param display_order: Determines the order parameters will be displayed in the UI.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_json(self):
        return super().to_json() | {
            "type": "integer",
        }


class StringCredentialParameter(CredentialParameter):
    def __init__(self, *args, **kwargs):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param credential_type: A group of credential parameters comprises a credential type. An adapter can have multiple types of credentials, which the user can choose between when creating an adapter instance. The default type is 'default_credential', which is useful for the common case where only one credential type is required.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param display_order: Determines the order parameters will be displayed in the UI.
        """
        super().__init__(*args, **kwargs)

    def to_json(self):
        return super().to_json() | {
            "type": "string",
        }


class PasswordCredentialParameter(CredentialParameter):
    def __init__(self, key: str, *args, **kwargs):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param credential_type: A group of credential parameters comprises a credential type. An adapter can have multiple types of credentials, which the user can choose between when creating an adapter instance. The default type is 'default_credential', which is useful for the common case where only one credential type is required.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param display_order: Determines the order parameters will be displayed in the UI.
        """
        super().__init__(key, *args, **kwargs)

    def to_json(self):
        return super().to_json() | {
            "type": "string",
            "password": True,
        }


class EnumCredentialParameter(CredentialParameter):
    """
    :param key: Used to identify the parameter.
    :param label: Label that is displayed in the vROps UI. Defaults to the key.
    :param credential_type: A group of credential parameters comprises a credential type. An adapter can have multiple types of credentials, which the user can choose between when creating an adapter instance. The default type is 'default_credential', which is useful for the common case where only one credential type is required.
    :param required: True if user is required to provide this parameter. Defaults to True.
    :param values: An array containing all enum values. If 'default' is specified and not part of this array, it
           will be added as an additional enum value. Enum values are not localizable.
    :param default: The default value of the enum.
    :param display_order: Determines the order parameters will be displayed in the UI.
    """
    def __init__(self, key: str, *args, values: list[str], default: str = None, **kwargs):
        super().__init__(key, *args, **kwargs)
        self.values = values
        self.default = default
        if default not in values:
            self.values.append(default)

    def to_json(self):
        return super().to_json() | {
            "type": "string",
            "default": self.default,
            "enum": True,
            "enum_values": [str(value) for value in self.values]
        }
