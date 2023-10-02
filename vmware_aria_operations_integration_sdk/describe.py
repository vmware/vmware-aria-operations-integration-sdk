#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import logging
import os
from collections import OrderedDict
from typing import Dict
from typing import Iterable
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING

import httpx
import lxml.etree as ET
from aria.ops.definition.units import UnitGroup
from aria.ops.definition.units import Units
from lxml.etree import Element
from lxml.etree import SubElement

if TYPE_CHECKING:
    from vmware_aria_operations_integration_sdk.adapter_container import (
        AdapterContainer,
    )
from vmware_aria_operations_integration_sdk.config import get_config_value
from vmware_aria_operations_integration_sdk.constant import (
    ADAPTER_DEFINITION_ENDPOINT,
    CONFIG_FILE_NAME,
)
from vmware_aria_operations_integration_sdk.constant import (
    CONFIG_DEFAULT_MEMORY_LIMIT_KEY,
)
from vmware_aria_operations_integration_sdk.logging_format import CustomFormatter
from vmware_aria_operations_integration_sdk.logging_format import PTKHandler
from vmware_aria_operations_integration_sdk.propertiesfile import load_properties

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = PTKHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)


class Describe:
    _path: str
    _adapter_container: Optional[AdapterContainer] = None
    _describe: Optional[Element]
    _resources: Dict[str, str]

    @classmethod
    def initialize(
        cls, path: str, adapter_container: Optional[AdapterContainer]
    ) -> None:
        cls._path = path
        cls._adapter_container = adapter_container
        cls._describe = None
        cls._resources = {}

    @classmethod
    async def get(cls, port: int) -> Tuple[Element, Dict]:
        if cls._describe is not None:
            return cls._describe, cls._resources
        describe_path = os.path.join(cls._path, "conf", "describe.xml")
        if os.path.exists(describe_path):
            cls._describe = ET.parse(describe_path).getroot()
            cls._resources = load_properties(
                os.path.join(cls._path, "conf", "resources", "resources.properties")
            )
        else:
            if not cls._adapter_container:
                raise Exception(
                    "Static describe.xml is not present, "
                    "but an AdapterContainer was not provided. Cannot "
                    "complete call to Describe.get()."
                )
            if not cls._adapter_container.started:
                cls._adapter_container.start()
                await cls._adapter_container.wait_for_container_startup()
                await cls._get_adapter_definition(port)
                await cls._adapter_container.stop()
            else:
                await cls._get_adapter_definition(port)
        return cls._describe, cls._resources

    @classmethod
    async def _get_adapter_definition(cls, port: int) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            from vmware_aria_operations_integration_sdk.containerized_adapter_rest_api import (
                send_get_to_adapter,
            )

            request, response, elapsed_time = await send_get_to_adapter(
                client, port, ADAPTER_DEFINITION_ENDPOINT
            )
            if not response.is_success:
                from vmware_aria_operations_integration_sdk.containerized_adapter_rest_api import (
                    get_failure_message,
                )

                logger.error(get_failure_message(response))
                logger.error(
                    f"adapterDefinition endpoint returned {response.status_code}."
                )
                if cls._adapter_container:
                    await cls._adapter_container.stop()
                exit(1)
            elif response.status_code == 204:
                logger.error(
                    f"adapterDefinition endpoint returned no response, indicating that the describe.xml file\n"
                    f"should be used, but no describe.xml file was found."
                )
                if cls._adapter_container:
                    await cls._adapter_container.stop()
                exit(1)
            adapter_definition = json.loads(response.text)
            describe, names = json_to_xml(adapter_definition)
            cls.merge_xml_fragments(describe, names)
            cls._describe = describe
            cls._resources = names.properties

    @classmethod
    def merge_xml_fragments(cls, describe: Element, names: _Names) -> None:
        # Note: All fragments must contain a top-level 'AdapterKind' element, and have the default namespace set to
        # 'http://schemas.vmware.com/vcops/schema'. Note: Any attributes on the 'AdapterKind' element itself will be
        # ignored. The 'AdapterKind' element only serves to hold one or more of the following fragment elements:
        elements = [
            "CustomGroupMetrics",
            "Faults",
            "LaunchConfigurations",
            "BasePolicyAnalysisSettings",
            "OOTBPolicies",
            "FavoriteGroups",
        ]

        for file in os.listdir(os.path.join(cls._path, "conf")):
            if file != "describe.xml" and file.endswith(".xml"):
                found_fragment = False
                logger.info(
                    "Adding describe fragment to describe.xml: "
                    + os.path.join(cls._path, "conf", file)
                )
                fragment = ET.parse(os.path.join(cls._path, "conf", file))

                # Names are handled separately because they will not be added to describe.xml, but instead
                # added to resources.properties. All elements with a 'nameKey' attribute *must* have a matching
                # /'Names'/'Name' element in the fragment. Name keys in each fragment will be remapped to ensure
                # there are no collisions between fragments and the primary describe.
                # Note: Support for Names in fragments is limited to the default translation/language
                namekey_remap = {}
                default_names = fragment.find(ns("Names"))  # Find first 'Names' element
                if default_names is not None:
                    fragment_names = default_names.findall(ns("Name"))
                    if fragment_names is not None and len(fragment_names) > 0:
                        for name in fragment_names:
                            namekey_remap[name.get("key")] = names.get_key(
                                name.get("shortName")
                            )

                for element in elements:
                    fragment_elements = fragment.find(ns(element))
                    if fragment_elements is not None and len(fragment_elements) > 0:
                        found_fragment = True
                        target_element = describe.find(ns(element))
                        if target_element is None:
                            target_element = SubElement(
                                describe,
                                element,
                            )
                        cls.remap_namekeys(fragment_elements, namekey_remap)
                        for fragment_element in fragment_elements:
                            target_element.append(fragment_element)
                if not found_fragment:
                    logger.warning(f"Ignoring file '{file}':")
                    logger.warning(
                        f"   XML file '{file}' did not contain any valid elements."
                    )
                    logger.warning(f"   Expected one or more of: {elements}")

    @staticmethod
    def remap_namekeys(element: Element, namekey_map: Dict) -> None:
        named_elements = element.findall(
            ".//*[@nameKey]"
        )  # Get all elements at any level with the attribute 'nameKey'
        for named_element in named_elements:
            new_key = namekey_map.get(named_element.get("nameKey"))
            if new_key is not None:
                named_element.set("nameKey", new_key)
            else:
                logger.warning(
                    f"Fragment error: No 'Name' element found with key '{named_element.get('nameKey')}'"
                )
                logger.warning(
                    f"Removing 'nameKey' from element {named_element.tag} {named_element.attrib}"
                )
                named_element.attrib.pop("nameKey")


def ns(kind: str) -> str:
    return "{http://schemas.vmware.com/vcops/schema}" + kind


def get_adapter_kind(describe: Element) -> Optional[str]:
    # TODO: if we get more than one adapter kind then we should considered it an error
    return describe.get("key")  # type: ignore


def get_adapter_instance(describe: Element) -> Optional[Element]:
    adapter_instance_kind = None

    for resource_kind in get_resource_kinds(describe):
        if resource_kind.get("type") == "7":
            adapter_instance_kind = resource_kind

    return adapter_instance_kind


def get_resource_kinds(describe: Element) -> Iterable[Element]:
    resource_kinds: Element = describe.find(ns("ResourceKinds"))
    if resource_kinds is not None:
        return resource_kinds.findall(ns("ResourceKind"))  # type: ignore
    return []


def get_identifiers(resource_kind: Element) -> Iterable[Element]:
    return resource_kind.findall(ns("ResourceIdentifier"))  # type: ignore


def get_credential_kinds(describe: Element) -> Iterable[Element]:
    credential_kinds = describe.find(ns("CredentialKinds"))
    if len(credential_kinds) > 0:
        return credential_kinds.findall(ns("CredentialKind"))  # type: ignore
    return []


def is_true(element: Element, attr: str, default: str = "false") -> bool:
    # The only valid lexical values for boolean are ["true", "false", "1", "0"] (case-sensitive)
    # https://www.w3.org/TR/xmlschema-2/#boolean
    return element.get(attr, default) in ["true", "1"]


def json_to_xml(json: Dict) -> Element:
    names = _Names()
    schema_version = int(json.get("schema_version", 0))

    describe = Element(
        ns("AdapterKind"),
        attrib={
            "key": json["adapter_key"],
            "nameKey": names.get_key(json["adapter_label"]),
            "version": str(json["describe_version"]),
        },
    )

    # CredentialKinds
    credential_kinds = SubElement(
        describe,
        ns("CredentialKinds"),
    )
    for credential_kind in json["credential_types"]:
        add_credential_kind(credential_kinds, credential_kind, names, schema_version)

    # ResourceKinds
    resource_kinds = SubElement(
        describe,
        ns("ResourceKinds"),
    )
    credential_types: Iterable[str] = map(
        lambda cred_type: str(cred_type["key"]), json["credential_types"]
    )
    add_resource_kind(
        resource_kinds,
        json["adapter_instance"],
        names,
        schema_version,
        type=7,
        credential_kinds=credential_types,
    )
    for object_type in json["object_types"]:
        add_resource_kind(resource_kinds, object_type, names, schema_version)

    # CustomGroupMetrics
    # CapacityDefinitions
    # Faults
    # LaunchConfigurations
    # add_launch_configurations(describe, names)
    # BasePolicyAnalysisSettings
    # UnitDefinitions
    add_units(describe, names)
    # OOTBPolicies
    # Names
    # FavoriteGroups

    return describe, names


def write_describe(describe: Element, filename: str) -> None:
    root = ET.ElementTree(describe)
    ET.indent(root)
    root.write(filename, encoding="utf-8", xml_declaration=True)


def add_credential_kind(
    parent: Element,
    credential_kind_json: Dict,
    names: _Names,
    schema_version: int,
) -> Element:
    xml = SubElement(
        parent,
        ns("CredentialKind"),
        attrib={
            "key": credential_kind_json["key"],
            "nameKey": names.get_key(credential_kind_json["label"]),
        },
    )
    for field in credential_kind_json["fields"]:
        field_xml = SubElement(
            xml,
            ns("CredentialField"),
            attrib={
                "key": field["key"],
                "nameKey": names.get_key(field["label"]),
                "required": str(field["required"]).lower(),
                "dispOrder": str(field["display_order"]),
                "password": str(field["password"]).lower(),
                "enum": str(field["enum"]).lower(),
                "type": str(field["type"]),
            },
        )
        add_enum_values(field_xml, field, names, schema_version)
    return xml


def add_resource_kind(
    parent: Element,
    resource_kind_json: Dict,
    names: _Names,
    schema_version: int,
    type: int = 1,
    credential_kinds: Optional[Iterable[str]] = None,
) -> Element:
    attributes = {
        "key": resource_kind_json["key"],
        "nameKey": names.get_key(resource_kind_json["label"]),
        "type": str(type),
    }
    if credential_kinds:
        attributes["credentialKind"] = ",".join(credential_kinds)

    resourcekind_xml = SubElement(
        parent,
        ns("ResourceKind"),
        attrib=attributes,
    )
    for identifier in resource_kind_json["identifiers"]:
        add_identifier(resourcekind_xml, identifier, names, schema_version)
    for attribute in resource_kind_json["attributes"]:
        add_attribute(resourcekind_xml, attribute, names)
    for group in resource_kind_json["groups"]:
        add_group(resourcekind_xml, group, names)
    return resourcekind_xml


def add_identifier(
    parent: Element,
    identifier_json: Dict,
    names: _Names,
    schema_version: int,
) -> Element:
    default = identifier_json.get("default")
    if default is None:
        default = ""
    identifier_xml = SubElement(
        parent,
        ns("ResourceIdentifier"),
        attrib={
            "default": str(default),
            "key": identifier_json["key"],
            "nameKey": names.get_key(
                identifier_json["label"], identifier_json.get("description")
            ),
            "required": str(identifier_json["required"]).lower(),
            "dispOrder": str(identifier_json["display_order"]),
            "enum": str(identifier_json["enum"]).lower(),
            "type": str(identifier_json["type"]),
            "identType": str(identifier_json["ident_type"]),
        },
    )
    add_enum_values(identifier_xml, identifier_json, names, schema_version)
    return identifier_xml


def add_enum_values(
    parent: Element, identifier_json: Dict, names: _Names, schema_version: int
) -> None:
    if "enum_values" in identifier_json:
        if schema_version >= 1:
            _add_enum_values_v1(parent, identifier_json, names)
        else:
            _add_enum_values_v0(parent, identifier_json, names)


def _add_enum_values_v0(parent: Element, identifier_json: Dict, names: _Names) -> None:
    for value in identifier_json["enum_values"]:
        SubElement(
            parent,
            ns("enum"),
            attrib={
                "value": str(value),
                "default": str(value == identifier_json.get("default", False)).lower(),
            },
        )


def _add_enum_values_v1(parent: Element, identifier_json: Dict, names: _Names) -> None:
    enum_values: list[dict[str, int]] = sorted(
        identifier_json["enum_values"], key=lambda value: value["display_order"]
    )
    for value in enum_values:
        SubElement(
            parent,
            ns("enum"),
            attrib={
                "value": str(value["key"]),
                "nameKey": names.get_key(str(value["label"])),
                "default": str(value == identifier_json.get("default", False)).lower(),
            },
        )


def add_attribute(parent: Element, attribute_json: Dict, names: _Names) -> Element:
    attribute_xml = SubElement(
        parent,
        ns("ResourceAttribute"),
        attrib={
            "key": attribute_json["key"],
            "nameKey": names.get_key(attribute_json["label"]),
            "unit": attribute_json.get("unit") or "",
            "dashboardOrder": str(attribute_json["dashboard_order"]),
            "dataType": str(attribute_json["data_type"]),
            "isProperty": str(attribute_json["is_property"]).lower(),
            "isRate": str(attribute_json["is_rate"]).lower(),
            "isDiscrete": str(attribute_json["is_discrete"]).lower(),
            "isImpact": str(attribute_json["is_impact"]).lower(),
            "defaultMonitored": str(True).lower(),
            "keyAttribute": str(attribute_json["is_key_attribute"]).lower(),
        },
    )
    return attribute_xml


def add_group(parent: Element, group_json: Dict, names: _Names) -> Element:
    group_xml = SubElement(
        parent,
        ns("ResourceGroup"),
        attrib={
            "key": group_json["key"],
            "nameKey": names.get_key(group_json["label"]),
            "instanced": str(group_json["instanced"]).lower(),
            "instanceRequired": str(group_json["instance_required"]).lower(),
        },
    )
    for subgroup in group_json.get("groups", []):
        add_group(group_xml, subgroup, names)
    for attribute in group_json.get("attributes", []):
        add_attribute(group_xml, attribute, names)
    return group_xml


def add_units(parent: Element, names: _Names) -> None:
    unit_definitions = SubElement(
        parent,
        ns("UnitDefinitions"),
    )
    add_unit_group(Units.RATIO, unit_definitions, names)
    add_unit_group(Units.TIME, unit_definitions, names)
    add_unit_group(Units.TIME_RATE, unit_definitions, names)
    add_unit_group(Units.RATE, unit_definitions, names)
    add_unit_group(Units.DATA_SIZE, unit_definitions, names)
    add_unit_group(Units.DATA_RATE, unit_definitions, names)
    add_unit_group(Units.FREQUENCY, unit_definitions, names)
    add_unit_group(Units.POWER, unit_definitions, names)
    add_unit_group(Units.ENERGY, unit_definitions, names)
    add_unit_group(Units.RESISTANCE, unit_definitions, names)
    add_unit_group(Units.VOLTAGE, unit_definitions, names)
    add_unit_group(Units.CURRENT, unit_definitions, names)
    add_unit_group(Units.CHARGE, unit_definitions, names)
    add_unit_group(Units.TEMPERATURE, unit_definitions, names)
    add_unit_group(Units.ROTATION_RATE, unit_definitions, names)
    add_unit_group(Units.MISC, unit_definitions, names)


def add_unit_group(cls: UnitGroup, root: Element, names: _Names) -> None:
    subtypes = set(map(lambda item: item.value._subtype, cls))  # type: ignore
    for subtype in subtypes:
        unit_type = SubElement(
            root,
            ns("UnitType"),
            key=cls.__name__ + subtype,
        )
        for unit in cls:
            if unit.value._subtype == subtype:
                SubElement(
                    unit_type,
                    ns("Unit"),
                    key=unit.value.key,
                    nameKey=names.get_key(unit.value.label),
                    order=str(unit.value._order),
                    conversionFactor=str(unit.value._conversion_factor),
                )


class _Names:
    def __init__(self) -> None:
        self._names: Dict[str, str] = {}
        self.properties: Dict[str, str] = OrderedDict()
        self._count: int = 0

    def get_key(self, name: str, description: Optional[str] = None) -> str:
        if name not in self._names:
            self._count += 1
            id = str(self._count)
            self._names[name] = id
        else:
            id = self._names[name]

        self.properties[id] = name
        if description is not None:
            self.properties[id + ".description"] = description
        return id
