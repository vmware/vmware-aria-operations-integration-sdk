#  Copyright 2022-2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import sys
from collections import OrderedDict
from typing import Optional

from aria.ops.definition.assertions import validate_key
from aria.ops.definition.credential_type import CredentialType
from aria.ops.definition.exceptions import DuplicateKeyException
from aria.ops.definition.exceptions import KeyException
from aria.ops.definition.group import GroupType
from aria.ops.definition.object_type import ObjectType
from aria.ops.definition.parameter import EnumParameter
from aria.ops.definition.parameter import IntParameter
from aria.ops.definition.parameter import Parameter
from aria.ops.definition.parameter import StringParameter
from aria.ops.pipe_utils import write_to_pipe


class AdapterDefinition(GroupType):  # type: ignore
    def __init__(
        self,
        key: str,
        label: Optional[str] = None,
        adapter_instance_key: Optional[str] = None,
        adapter_instance_label: Optional[str] = None,
        version: int = 1,
    ):
        """
        Args:
            key (str): The adapter key is used to identify the adapter and its object types. It must be unique across
                all Management Packs.
            label (Optional[str]): Label that is displayed in the VMware Aria Operations UI for this adapter.
                Defaults to the key.
            adapter_instance_key (Optional[str]): Object type of the adapter instance object. Defaults to
                '{adapter key}_adapter_instance'.
            adapter_instance_label (Optional[str]): Label that is displayed in the VMware Aria Operations UI for the
                adapter instance object type. Defaults to '{adapter label} Adapter Instance'.
            version (int): Version of the definition. This should be incremented for new releases of the adapter.
                Defaults to 1
        """
        key = validate_key(key, "Adapter")
        if not key[0].isalpha():
            raise KeyException("Adapter key must start with a letter.")
        if len(key.split()) > 1:
            raise KeyException("Adapter key cannot contain whitespace.")
        if not all(c.isalnum() or c == "_" for c in key):
            raise KeyException(
                "Adapter key cannot contain special characters besides '_'."
            )

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
        self.parameters: dict = OrderedDict()
        self.credentials: dict = {}
        self.object_types: dict = {}

        super().__init__()

    def to_json(self) -> dict:
        return {
            "adapter_key": self.key,
            "adapter_label": self.label,
            "describe_version": self.version,
            "schema_version": 1,
            "adapter_instance": {
                "key": self.adapter_instance_key,
                "label": self.adapter_instance_label,
                "identifiers": [
                    identifier.to_json() for identifier in self.parameters.values()
                ],
            }
            | super().to_json(),
            "credential_types": [
                credential_type.to_json()
                for credential_type in self.credentials.values()
            ],
            "object_types": [
                object_type.to_json() for object_type in self.object_types.values()
            ],
        }

    def send_results(self, output_pipe: str = sys.argv[-1]) -> None:
        """Opens the output pipe and sends results directly back to the server

        This method can only be called once per server request.
        """
        # The server always invokes methods with the output file as the last argument
        write_to_pipe(output_pipe, self.to_json())

    def define_string_parameter(
        self,
        key: str,
        label: Optional[str] = None,
        description: Optional[str] = None,
        default: Optional[str] = None,
        max_length: int = 512,
        required: bool = True,
        advanced: bool = False,
    ) -> StringParameter:
        """
        Create a new string parameter and add it to the adapter instance. The user will be asked to provide a value for
        this parameter each time a new account/adapter instance is created.

        Args:
            key (str): Used to identify the parameter
            label (Optional[str]): Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
            description (Optional[str]): More in-depth explanation of the parameter. Displayed as a tooltip in the
                VMware Aria Operations UI.
            default (Optional[str]): The default value of the parameter. Defaults to None
            max_length (int): The max length of the parameter value. Defaults to 512.
            required (bool): True if user is required to provide this parameter. Defaults to True.
            advanced (bool): True if the parameter should be collapsed by default. Defaults to False.

        Returns:
             The created string parameter definition.
        """
        parameter = StringParameter(
            key,
            label,
            description,
            default,
            max_length,
            required,
            advanced,
            display_order=len(self.parameters),
        )
        self.add_parameter(parameter)
        return parameter

    def define_int_parameter(
        self,
        key: str,
        label: Optional[str] = None,
        description: Optional[str] = None,
        default: Optional[int] = None,
        required: bool = True,
        advanced: bool = False,
    ) -> IntParameter:
        """
        Create a new integer parameter and add it to the adapter instance. The user will be asked to provide a value for
        this parameter each time a new account/adapter instance is created.

        Args:
            key (str): Used to identify the parameter
            label (Optional[str]): Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
            description (Optional[str]): More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
            default (Optional[int]): The default value of the parameter.
            required (bool): True if user is required to provide this parameter. Defaults to True.
            advanced (bool): True if the parameter should be collapsed by default. Defaults to False.

        Returns:
             The created int parameter definition.
        """
        parameter = IntParameter(
            key,
            label,
            description,
            default,
            required,
            advanced,
            display_order=len(self.parameters),
        )
        self.add_parameter(parameter)
        return parameter

    def define_enum_parameter(
        self,
        key: str,
        values: list[str],
        label: Optional[str] = None,
        description: Optional[str] = None,
        default: Optional[str] = None,
        required: bool = True,
        advanced: bool = False,
    ) -> EnumParameter:
        """
        Create a new enum parameter and add it to the adapter instance. The user will be asked to provide a value for
        this parameter each time a new account/adapter instance is created.

        Args:
            key (str): Used to identify the parameter
            values (List[str]): An array containing all enum values. If 'default' is specified and not part of this array, it
                will be added as an additional enum value (values are case-sensitive). Enum values are not localizable.
            label (Optional[str]): Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
            description (Optional[str]): More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
            default (Optional[str]): The default value of the parameter.
            required (bool): True if user is required to provide this parameter. Defaults to True.
            advanced (bool): True if the parameter should be collapsed by default. Defaults to False.

        Returns:
             The created enum parameter definition.
        """
        parameter = EnumParameter(
            key,
            values,
            label,
            description,
            default,
            required,
            advanced,
            display_order=len(self.parameters),
        )
        self.add_parameter(parameter)
        return parameter

    def add_parameter(self, parameter: Parameter) -> None:
        """
        Add a parameter to the adapter instance. The user will be asked to provide a value for
        this parameter each time a new account/adapter instance is created.

        Args:
            parameter (Parameter): The parameter to add to the adapter instance.
        """
        key = parameter.key
        if key in self.parameters:
            raise DuplicateKeyException(
                f"Parameter with key {key} already exists in adapter definition."
            )
        self.parameters[key] = parameter

    def define_credential_type(
        self, key: str = "default_credential", label: Optional[str] = None
    ) -> CredentialType:
        """
        Create a new credential type and add it to this adapter instance. When more than one credential types are
        present, The user will be required to select the type and then fill in the parameters for that type, as only
        one credential type can be used for any given adapter instance.

        Args:
            key (str): Used to identify the credential type
            label (Optional[str]): Label that is displayed in the VMware Aria Operations UI. Defaults to the key.

        Returns:
             The created credential type.
        """
        credential = CredentialType(key, label)
        self.add_credential_type(credential)
        return credential

    def add_credential_types(self, credential_types: list[CredentialType]) -> None:
        """
        Add a list of credential types to the adapter instance.

        Args:
            credential_types (List[CredentialType]): A list of credential types to add.
        """
        for credential_type in credential_types:
            self.add_credential_type(credential_type)

    def add_credential_type(self, credential_type: CredentialType) -> None:
        """
        Add a credential type to the adapter instance. When more than one credential types are present, The user will
        be required to select the type and then fill in the parameters for that type, as only one credential type can be
        used for any given adapter instance.

        Args:
            credential_type (CredentialType): The credential type to add.
        """
        key = credential_type.key
        if key in self.credentials:
            raise DuplicateKeyException(
                f"Credential type with key {key} already exists in adapter definition."
            )
        self.credentials[key] = credential_type

    def define_object_type(self, key: str, label: Optional[str] = None) -> ObjectType:
        """
        Create a new object type definition and add it to this adapter definition.

        Args:
            key (str): The object type
            label (Optional[str]): Label that is displayed in the VMware Aria Operations UI for this object type. Defaults to the key.

        Returns:
             The created object type definition
        """
        object_type = ObjectType(key, label)
        self.add_object_type(object_type)
        return object_type

    def add_object_types(self, object_types: list[ObjectType]) -> None:
        """
        Adds a list of object types to this adapter definition
        Args:
            object_types (List[ObjectType]): A list of object type definitions.
        """
        for object_type in object_types:
            self.add_object_type(object_type)

    def add_object_type(self, object_type: ObjectType) -> None:
        """
        Adds an object type to this adapter definition

        Args:
            object_type (ObjectType): An object type definition.
        """
        key = object_type.key
        if key in self.object_types:
            raise DuplicateKeyException(
                f"Object type with key {key} already exists in adapter definition."
            )
        self.object_types[key] = object_type
