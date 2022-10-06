#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import OrderedDict

from vrops.definition.assertions import validate_key
from vrops.definition.credential_type import CredentialType
from vrops.definition.exceptions import KeyException, DuplicateKeyException
from vrops.definition.group import GroupType
from vrops.definition.object_type import ObjectType
from vrops.definition.parameter import StringParameter, IntParameter, EnumParameter, Parameter


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
        :param label: Label that is displayed in the VMware Aria Operations UI for this adapter. Defaults to the key.
        :param adapter_instance_key: Object type of the adapter instance object. Defaults to
               '{adapter key}_adapter_instance'.
        :param adapter_instance_label: Label that is displayed in the VMware Aria Operations UI for the adapter instance
               object type. Defaults to '{adapter label} Adapter Instance'.
        :param version: Version of the definition. This should be incremented for new releases of the adapter.
        """
        key = validate_key(key, "Adapter")
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
            "credential_types": [credential_type.to_json() for credential_type in self.credentials.values()],
            "object_types": [object_type.to_json() for object_type in self.object_types.values()]
        }

    def define_string_parameter(self, key: str, label: str = None, description: str = None, default: str = None,
                                required: bool = True, advanced: bool = False):
        """
        Create a new string parameter and add it to the adapter instance. The user will be asked to provide a value for
        this parameter each time a new account/adapter instance is created.
        :param key: Used to identify the parameter
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
        :param default: The default value of the parameter.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :return The created string parameter definition.
        """
        parameter = StringParameter(key, label, description, default, required, advanced,
                                    display_order=len(self.parameters))
        self.add_parameter(parameter)
        return parameter

    def define_int_parameter(self, key: str, label: str = None, description: str = None,
                             default: int = None, required: bool = True, advanced: bool = False):
        """
        Create a new integer parameter and add it to the adapter instance. The user will be asked to provide a value for
        this parameter each time a new account/adapter instance is created.
        :param key: Used to identify the parameter
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
        :param default: The default value of the parameter.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :return The created int parameter definition.
        """
        parameter = IntParameter(key, label, description, default, required, advanced,
                                 display_order=len(self.parameters))
        self.add_parameter(parameter)
        return parameter

    def define_enum_parameter(self, key: str, values: list[str], label: str = None, description: str = None,
                              default: str = None, required: bool = True, advanced: bool = False):
        """
        Create a new enum parameter and add it to the adapter instance. The user will be asked to provide a value for
        this parameter each time a new account/adapter instance is created.
        :param key: Used to identify the parameter
        :param values: An array containing all enum values. If 'default' is specified and not part of this array, it
               will be added as an additional enum value (values are case-sensitive). Enum values are not localizable.
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
        :param default: The default value of the parameter.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :return The created enum parameter definition.
        """
        parameter = EnumParameter(key, values, label, description, default, required, advanced,
                                  display_order=len(self.parameters))
        self.add_parameter(parameter)
        return parameter

    def add_parameter(self, parameter: Parameter):
        """
        Add a parameter to the adapter instance. The user will be asked to provide a value for
        this parameter each time a new account/adapter instance is created.
        :param parameter: The parameter to add to the adapter instance.
        :return: None
        """
        key = parameter.key
        if key in self.parameters:
            raise DuplicateKeyException(f"Parameter with key {key} already exists in adapter definition.")
        self.parameters[key] = parameter

    def define_credential_type(self, key: str = "default_credential", label: str = None):
        """
        Create a new credential type and add it to this adapter instance. When more than one credential types are
        present, The user will be required to select the type and then fill in the parameters for that type, as only
        one credential type can be used for any given adapter instance.
        :param key: Used to identify the credential type
        :param label: Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
        :return The created credential type.
        """
        credential = CredentialType(key, label)
        self.add_credential_type(credential)
        return credential

    def add_credential_types(self, credential_types: list[CredentialType]):
        """
        Add a list of credential types to the adapter instance.
        :param credential_types: A list of credential types to add.
        :return: None
        """
        for credential_type in credential_types:
            self.add_credential_type(credential_type)

    def add_credential_type(self, credential_type: CredentialType):
        """
        Add a credential type to the adapter instance. When more than one credential types are present, The user will
        be required to select the type and then fill in the parameters for that type, as only one credential type can be
        used for any given adapter instance.
        :param credential_type: The credential type to add.
        :return: None
        """
        key = credential_type.key
        if key in self.credentials:
            raise DuplicateKeyException(f"Credential type with key {key} already exists in adapter definition.")
        self.credentials[key] = credential_type

    def define_object_type(self, key: str, label: str = None):
        """
        Create a new object type definition and add it to this adapter definition.
        :param key: The object type
        :param label: Label that is displayed in the VMware Aria Operations UI for this object type. Defaults to the key.
        :return: The created object type definition
        """
        object_type = ObjectType(key, label)
        self.add_object_type(object_type)
        return object_type

    def add_object_types(self, object_types: list[ObjectType]):
        """
        Adds a list of object types to this adapter definition
        :param object_types: A list of object type definitions.
        :return: None
        """
        for object_type in object_types:
            self.add_object_type(object_type)

    def add_object_type(self, object_type: ObjectType):
        """
        Adds an object type to this adapter definition
        :param object_type: An object type definition.
        :return: None
        """
        key = object_type.key
        if key in self.object_types:
            raise DuplicateKeyException(f"Object type with key {key} already exists in adapter definition.")
        self.object_types[key] = object_type
