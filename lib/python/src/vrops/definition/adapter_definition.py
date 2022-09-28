#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from abc import ABC
from collections import OrderedDict

from vrops.definition.credential import StringCredentialParameter, IntCredentialParameter, PasswordCredentialParameter, \
    EnumCredentialParameter, CredentialParameter
from vrops.definition.group import GroupType
from vrops.definition.object_definition import ObjectDefinition
from vrops.definition.parameter import StringParameter, IntParameter, EnumParameter


class KeyException(Exception):
    pass


class AdapterDefinition(GroupType):
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
        self.parameters = OrderedDict()
        self.credentials = {}
        self.object_types = {}

        super().__init__()

    def to_json(self):
        return {
            "adapter_key": self.key,
            "adapter_label": self.label,
            "describe_version": self.version,
            "adapter_instance": {
                "key": self.adapter_instance_key,
                "label": self.adapter_instance_label,
                "identifiers": [identifier.to_json() for identifier in self.parameters.values()],
            } | super().to_json(),
            "credential_types": [
                {
                    "credential_type": credential_type,
                    "fields": [field.to_json() for field in self.credentials.get(credential_type, {}).values()]
                }
                for credential_type in self.credentials.keys()
            ],
            "object_types": [object_type.to_json() for object_type in self.object_types.values()]
        }

    def string_parameter(self, key, *args, **kwargs):
        """
        :param key: Used to identify the parameter
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the vROps UI.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :param default: The default value of the parameter.
        """
        self.parameters[key] = StringParameter(key, *args, **kwargs, display_order=len(self.parameters))

    def int_parameter(self, key, *args, **kwargs):
        """
        :param key: Used to identify the parameter
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the vROps UI.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :param default: The default value of the parameter.
        """
        self.parameters[key] = IntParameter(key, *args, **kwargs, display_order=len(self.parameters))

    def enum_parameter(self, key, *args, **kwargs):
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
        self.parameters[key] = EnumParameter(key, *args, **kwargs, display_order=len(self.parameters))

    def string_credential_parameter(self, key, *args, **kwargs):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param credential_type: A group of credential parameters comprises a credential type. An adapter can have multiple types of credentials, which the user can choose between when creating an adapter instance. The default type is 'default_credential', which is useful for the common case where only one credential type is required.
        :param required: True if user is required to provide this parameter. Defaults to True.
        """
        self._add_credential(StringCredentialParameter(key, *args, **kwargs))

    def int_credential_parameter(self, key, *args, **kwargs):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param credential_type: A group of credential parameters comprises a credential type. An adapter can have multiple types of credentials, which the user can choose between when creating an adapter instance. The default type is 'default_credential', which is useful for the common case where only one credential type is required.
        :param required: True if user is required to provide this parameter. Defaults to True.
        """
        self._add_credential(IntCredentialParameter(key, *args, **kwargs))

    def password_credential_parameter(self, key, *args, **kwargs):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param credential_type: A group of credential parameters comprises a credential type. An adapter can have multiple types of credentials, which the user can choose between when creating an adapter instance. The default type is 'default_credential', which is useful for the common case where only one credential type is required.
        :param required: True if user is required to provide this parameter. Defaults to True.
        """
        self._add_credential(PasswordCredentialParameter(key, *args, **kwargs))

    def enum_credential_parameter(self, key, *args, **kwargs):
        """
        :param key: Used to identify the parameter.
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param credential_type: A group of credential parameters comprises a credential type. An adapter can have multiple types of credentials, which the user can choose between when creating an adapter instance. The default type is 'default_credential', which is useful for the common case where only one credential type is required.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param values: An array containing all enum values. If 'default' is specified and not part of this array, it
               will be added as an additional enum value. Enum values are not localizable.
        :param default: The default value of the enum.
        """
        self._add_credential(EnumCredentialParameter(key, *args, **kwargs))

    def _add_credential(self, credential_parameter: CredentialParameter):
        key = credential_parameter.key
        credential_type = credential_parameter.credential_type
        self.credentials.setdefault(credential_type, OrderedDict())
        credential_parameter.display_order = len(self.credentials[credential_type])
        self.credentials[credential_type][key] = credential_parameter

    def object_type(self, key, *args, **kwargs):
        if key in self.object_types:
            return self.object_types.get(key)
        object_type = ObjectDefinition(key, *args, **kwargs)
        self.object_types[key] = object_type
        return object_type
