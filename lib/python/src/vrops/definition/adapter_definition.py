#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from abc import ABC


class KeyException(Exception):
    pass


class Parameter(ABC):
    def __init__(self,
                 key: str,
                 label: str = None,
                 description: str = None,
                 required: bool = True,
                 advanced: bool = False,
                 default: str | int = None,
                 display_order: int = 0):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the vROps UI.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :param default: The default value of the parameter.
        :param display_order: Determines the order parameters will be displayed in the UI.
        """
        self.key = key
        self.label = label
        if label is None:
            self.label = key
        self.description = description
        self.required = required
        self.advanced = advanced
        self.display_order = display_order
        self.default = default

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
    def __init__(self, key: str, *args, default: int = None, **kwargs):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the vROps UI.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :param default: The default value of the parameter.
        :param display_order: Determines the order parameters will be displayed in the UI.
        """
        super().__init__(key, *args, default=default, **kwargs)

    def to_json(self):
        return super().to_json() | {
            "type": "integer",
            "default": int(self.default),
        }


class StringParameter(Parameter):
    def __init__(self, key: str, *args, default: str = None, max_length: int = None, **kwargs):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the vROps UI.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :param default: The default value of the parameter.
        :param display_order: Determines the order parameters will be displayed in the UI.
        """
        super().__init__(key, *args, default=default, **kwargs)
        self.max_length = max_length

    def to_json(self):
        return super().to_json() | {
            "type": "string",
            "length": self.max_length,
            "default": str(self.default)
        }


class EnumParameter(Parameter):
    def __init__(self, key: str, *args, values: list[str], default: str = None, **kwargs):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the vROps UI.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :param values: An array containing all enum values. If 'default' is specified and not part of this array, it
               will be added as an additional enum value. Enum values are not localizable.
        :param default: The default value of the parameter.
        :param display_order: Determines the order parameters will be displayed in the UI.
        """
        super().__init__(key, *args, default=default, **kwargs)
        self.values = values
        if default not in self.values:
            self.values.append(default)

    def to_json(self):
        return super().to_json() | {
            "type": "string",
            "enum": True,
            "enum_values": [str(value) for value in self.values]
        }


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


class AdapterDefinition:
    def __init__(self,
                 key: str,
                 label: str = None,
                 adapter_instance_key: str = None,
                 adapter_instance_label: str = None,
                 version: int = 1):
        """
        :param key: The adapter key is used to identify the adapter and its object types. It must be unique across
               all Management Packs.
        :param label: Label that is displayed in the vROps UI for this adapter. Defaults to the key.
        :param adapter_instance_key: Object type of the adapter instance object. Defaults to
               '{adapter key}_adapter_instance'.
        :param adapter_instance_label: Label that is displayed in the vROps UI for the adapter instance object type.
               Defaults to '{adapter label} Adapter Instance'.
        :param version: Version of the definition. This should be incremented for new releases of the adapter.
        """
        if key is None:
            raise KeyException("Adapter key cannot be 'None'.")
        if type(key) is not str:
            raise KeyException("Adapter key must be a string.")
        if key == "":
            raise KeyException("Adapter key cannot be empty.")
        if key.isspace():
            raise KeyException("Adapter key cannot be blank.")
        if not key[0].isalpha():
            raise KeyException("Adapter key must start with a letter.")
        if len(key.split()) > 1:
            raise KeyException("Adapter key cannot contain whitespace.")
        if not all(c.isalnum() or c == "_" for c in key):
            raise KeyException("Adapter key cannot contain special characters besides '_'.")

        self.key = key

        self.label = label
        if label is None:
            self.label = key

        self.adapter_instance_key = adapter_instance_key
        if adapter_instance_key is None:
            self.adapter_instance_key = f"{self.key}_adapter_instance"

        self.adapter_instance_label = adapter_instance_label
        if adapter_instance_label is None:
            self.adapter_instance_label = f"{self.label} Adapter Instance"

        self.version = version
        self.parameters = []
        self.credentials = {}

    def to_json(self):
        return {
            "adapter_key": self.key,
            "adapter_label": self.label,
            "describe_version": self.version,
            "adapter_instance": {
                "key": self.adapter_instance_key,
                "label": self.adapter_instance_label,
                "identifiers": [identifier.to_json() for identifier in self.parameters]
            },
            "credential_types": [
                {
                    "credential_type": credential_type,
                    "fields": [field.to_json() for field in self.credentials[credential_type]]
                }
                for credential_type in self.credentials.keys()
            ]
        }

    def string_parameter(self, *args, **kwargs):
        """
        :param key: Used to identify the parameter
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the vROps UI.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :param default: The default value of the parameter.
        """
        self.parameters.append(StringParameter(*args, **kwargs, display_order=len(self.parameters)))

    def int_parameter(self, *args, **kwargs):
        """
        :param key: Used to identify the parameter
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the vROps UI.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :param default: The default value of the parameter.
        """
        self.parameters.append(IntParameter(*args, **kwargs, display_order=len(self.parameters)))

    def enum_parameter(self, *args, **kwargs):
        """
        :param key: Used to identify the parameter
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the vROps UI.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :param default: The default value of the parameter.
        :param values: An array containing all enum values. If 'default' is specified and not part of this array, it
               will be added as an additional enum value (values are case-sensitive). Enum values are not localizable.
        """
        self.parameters.append(EnumParameter(*args, **kwargs, display_order=len(self.parameters)))

    def string_credential_parameter(self, *args, **kwargs):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param credential_type: A group of credential parameters comprises a credential type. An adapter can have multiple types of credentials, which the user can choose between when creating an adapter instance. The default type is 'default_credential', which is useful for the common case where only one credential type is required.
        :param required: True if user is required to provide this parameter. Defaults to True.
        """
        self._add_credential(StringCredentialParameter(*args, **kwargs))

    def int_credential_parameter(self, *args, **kwargs):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param credential_type: A group of credential parameters comprises a credential type. An adapter can have multiple types of credentials, which the user can choose between when creating an adapter instance. The default type is 'default_credential', which is useful for the common case where only one credential type is required.
        :param required: True if user is required to provide this parameter. Defaults to True.
        """
        self._add_credential(IntCredentialParameter(*args, **kwargs))

    def password_credential_parameter(self, *args, **kwargs):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param credential_type: A group of credential parameters comprises a credential type. An adapter can have multiple types of credentials, which the user can choose between when creating an adapter instance. The default type is 'default_credential', which is useful for the common case where only one credential type is required.
        :param required: True if user is required to provide this parameter. Defaults to True.
        """
        self._add_credential(PasswordCredentialParameter(*args, **kwargs))

    def enum_credential_parameter(self, *args, **kwargs):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param credential_type: A group of credential parameters comprises a credential type. An adapter can have multiple types of credentials, which the user can choose between when creating an adapter instance. The default type is 'default_credential', which is useful for the common case where only one credential type is required.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param values: An array containing all enum values. If 'default' is specified and not part of this array, it
               will be added as an additional enum value. Enum values are not localizable.
        :param default: The default value of the enum.
        """
        self._add_credential(EnumCredentialParameter(*args, **kwargs))

    def _add_credential(self, credential_parameter: CredentialParameter):
        credential_type = credential_parameter.credential_type
        self.credentials.setdefault(credential_type, [])
        credential_parameter.display_order = len(self.credentials[credential_type])
        self.credentials[credential_type].append(credential_parameter)

