#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import OrderedDict

from vrops.definition.group import GroupType
from vrops.definition.parameter import EnumParameter, IntParameter, StringParameter


class ObjectDefinition(GroupType):
    def __init__(self,
                 key: str,
                 label: str):
        self.key = key
        self.label = label
        self.identifiers = OrderedDict()
        super().__init__()

    def string_identifier(self, key, *args, **kwargs) -> ObjectDefinition:
        """
        :param key: Used to identify the parameter
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the vROps UI.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :param default: The default value of the parameter.
        """
        self.identifiers[key] = StringParameter(key, *args, **kwargs, display_order=len(self.identifiers))
        return self

    def int_identifier(self, key, *args, **kwargs) -> ObjectDefinition:
        """
        :param key: Used to identify the parameter
        :param label: Label that is displayed in the vROps UI. Defaults to the key.
        :param description: More in-depth explanation of the parameter. Displayed as a tooltip in the vROps UI.
        :param required: True if user is required to provide this parameter. Defaults to True.
        :param advanced: True if the parameter should be collapsed by default. Defaults to False.
        :param default: The default value of the parameter.
        """
        self.identifiers[key] = IntParameter(key, *args, **kwargs, display_order=len(self.identifiers))
        return self

    def enum_identifier(self, key, *args, **kwargs) -> ObjectDefinition:
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
        self.identifiers[key] = EnumParameter(key, *args, **kwargs, display_order=len(self.identifiers))
        return self

    def to_json(self):
        return {
            "key": self.key,
            "label": self.label,
            "identifiers": [identifier.to_json() for identifier in self.identifiers.values()],
        } | super().to_json()
