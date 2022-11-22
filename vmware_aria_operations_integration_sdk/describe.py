#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import logging
import os
from collections import OrderedDict
from typing import Optional

import lxml.etree as ET
from lxml.etree import Element, SubElement

import httpx

from aria.ops.definition.units import Units
from vmware_aria_operations_integration_sdk.config import get_config_value
from vmware_aria_operations_integration_sdk.constant import ADAPTER_DEFINITION_ENDPOINT
from vmware_aria_operations_integration_sdk.logging_format import PTKHandler, CustomFormatter
from vmware_aria_operations_integration_sdk.propertiesfile import load_properties

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = PTKHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)


class Describe:
    _path: str
    _adapter_container = None  # : AdapterContainer
    _describe: Optional[Element]
    _resources: {str: str}

    @classmethod
    def initialize(cls, path, adapter_container):
        cls._path = path
        cls._adapter_container = adapter_container
        cls._describe = None
        cls._resources = {}

    @classmethod
    async def get(cls):
        if cls._describe is not None:
            return cls._describe, cls._resources
        describe_path = os.path.join(cls._path, "conf", "describe.xml")
        if os.path.exists(describe_path):
            cls._describe = ET.parse(describe_path).getroot()
            cls._resources = load_properties(os.path.join(cls._path, "conf", "resources", "resources.properties"))
        else:
            if not cls._adapter_container.started:
                memory_limit = get_config_value("default_memory_limit", 1024, os.path.join(cls._path, "config.json"))
                cls._adapter_container.start(memory_limit)
                await cls._adapter_container.wait_for_container_startup()
                await cls._get_adapter_definition()
                await cls._adapter_container.stop()
            else:
                await cls._get_adapter_definition()
        return cls._describe, cls._resources

    @classmethod
    async def _get_adapter_definition(cls):
        async with httpx.AsyncClient(timeout=30) as client:
            from vmware_aria_operations_integration_sdk.containerized_adapter_rest_api import send_get_to_adapter
            request, response, elapsed_time = await send_get_to_adapter(client, ADAPTER_DEFINITION_ENDPOINT)
            if not response.is_success:
                from vmware_aria_operations_integration_sdk.containerized_adapter_rest_api import get_failure_message
                logger.error(get_failure_message(response))
                logger.error(f"adapterDefinition endpoint returned {response.status_code}.")
                await cls._adapter_container.stop()
                exit(1)
            elif response.status_code == 204:
                logger.error(f"adapterDefinition endpoint returned no response, indicating that the describe.xml file\n"
                             f"should be used, but no describe.xml file was found.")
                await cls._adapter_container.stop()
                exit(1)
            adapter_definition = json.loads(response.text)
            describe, names = json_to_xml(adapter_definition)
            cls.merge_xml_fragments(describe, names)
            cls._describe = describe
            cls._resources = names.properties

    @classmethod
    def merge_xml_fragments(cls, describe, names):
        # Note: All fragments must contain a top-level 'AdapterKind' element, and have the default namespace set to
        # 'http://schemas.vmware.com/vcops/schema'. Note: Any attributes on the 'AdapterKind' element itself will be
        # ignored. The 'AdapterKind' element only serves to hold one or more of the following fragment elements:
        elements = ["CustomGroupMetrics",
                    "Faults",
                    "LaunchConfigurations",
                    "BasePolicyAnalysisSettings",
                    "OOTBPolicies",
                    "FavoriteGroups"]

        for file in os.listdir(os.path.join(cls._path, "conf")):
            if file != "describe.xml" and file.endswith(".xml"):
                found_fragment = False
                logger.info("Adding describe fragment to describe.xml: " + os.path.join(cls._path, "conf", file))
                fragment = ET.parse(os.path.join(cls._path, "conf", file))

                # Names are handled separately because they will not be added to describe.xml, but instead
                # added to resources.properties. All elements with a 'nameKey' attribute *must* have a matching
                # /'Names'/'Name' element in the fragment. Name keys in each fragment will be remapped to ensure
                # there are no collisions between fragments and the primary describe.
                # Note: Support for Names in fragments is limited to the default translation/language
                namekey_remap = {}
                default_names = fragment.find(ns('Names'))  # Find first 'Names' element
                if default_names is not None:
                    fragment_names = default_names.findall(ns('Name'))
                    if fragment_names is not None and len(fragment_names) > 0:
                        for name in fragment_names:
                            namekey_remap[name.get("key")] = names.get_key(name.get("shortName"))

                for element in elements:
                    fragment_elements = fragment.find(ns(element))
                    if fragment_elements is not None and len(fragment_elements) > 0:
                        found_fragment = True
                        target_element = describe.find(ns(element))
                        if target_element is None:
                            target_element = SubElement(describe, element, nsmap=ns_map)
                        cls.remap_namekeys(fragment_elements, namekey_remap)
                        for fragment_element in fragment_elements:
                            target_element.append(fragment_element)
                if not found_fragment:
                    logger.warning(f"Ignoring file '{file}':")
                    logger.warning(f"   XML file '{file}' did not contain any valid elements.")
                    logger.warning(f"   Expected one or more of: {elements}")

    @staticmethod
    def remap_namekeys(element, namekey_map):
        named_elements = element.findall(".//*[@nameKey]")  # Get all elements at any level with the attribute 'nameKey'
        for named_element in named_elements:
            new_key = namekey_map.get(named_element.get("nameKey"))
            if new_key is not None:
                named_element.set("nameKey", new_key)
            else:
                logger.warning(f"Fragment error: No 'Name' element found with key '{named_element.get('nameKey')}'")
                logger.warning(f"Removing 'nameKey' from element {named_element.tag} {named_element.attrib}")
                named_element.attrib.pop("nameKey")


def ns(kind):
    return "{*}" + kind


ns_map = {None: "http://schemas.vmware.com/vcops/schema"}


def get_adapter_kind(describe):
    # TODO: if we get more than one adapter kind then we should considered it an error
    return describe.get("key")


def get_adapter_instance(describe):
    adapter_instance_kind = None

    for resource_kind in get_resource_kinds(describe):
        if resource_kind.get("type") == "7":
            adapter_instance_kind = resource_kind

    return adapter_instance_kind


def get_resource_kinds(describe):
    return describe.find(ns("ResourceKinds")).findall(ns("ResourceKind"))


def get_identifiers(resource_kind):
    return resource_kind.findall(ns("ResourceIdentifier"))


def get_credential_kinds(describe):
    credential_kinds = describe.find(ns("CredentialKinds"))
    if credential_kinds is None:
        return None
    else:
        return credential_kinds.findall(ns("CredentialKind"))


def is_true(element, attr, default="false"):
    # The only valid lexical values for boolean are ["true", "false", "1", "0"] (case-sensitive)
    # https://www.w3.org/TR/xmlschema-2/#boolean
    return element.get(attr, default) in ["true", "1"]


def json_to_xml(json):
    names = _Names()
    describe = Element("{http://schemas.vmware.com/vcops/schema}AdapterKind", attrib={
        "key": json["adapter_key"],
        "nameKey": names.get_key(json["adapter_label"]),
        "version": str(json["describe_version"])
    }, nsmap=ns_map)

    # CredentialKinds
    credential_kinds = SubElement(describe, "CredentialKinds", nsmap=ns_map)
    for credential_kind in json["credential_types"]:
        add_credential_kind(credential_kinds, credential_kind, names)

    # ResourceKinds
    resource_kinds = SubElement(describe, "ResourceKinds", nsmap=ns_map)
    credential_types = map(lambda cred_type: cred_type["key"], json["credential_types"])
    add_resource_kind(resource_kinds, json["adapter_instance"], names, type=7, credential_kinds=credential_types)
    for object_type in json["object_types"]:
        add_resource_kind(resource_kinds, object_type, names)

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


def write_describe(describe, filename: str):
    root = ET.ElementTree(describe)
    ET.indent(root)
    root.write(filename, encoding='utf-8', xml_declaration=True)


def add_credential_kind(parent, credential_kind_json, names):
    xml = SubElement(parent, "CredentialKind", attrib={
        "key": credential_kind_json["key"],
        "nameKey": names.get_key(credential_kind_json["label"])
    }, nsmap=ns_map)
    for field in credential_kind_json["fields"]:
        field_xml = SubElement(xml, "CredentialField", attrib={
            "key": field["key"],
            "nameKey": names.get_key(field["label"]),
            "required": str(field["required"]).lower(),
            "dispOrder": str(field["display_order"]),
            "password": str(field["password"]).lower(),
            "enum": str(field["enum"]).lower(),
            "type": str(field["type"])
        }, nsmap=ns_map)
        add_enum_values(field_xml, field)
    return xml


def add_resource_kind(parent, resource_kind_json, names, type=1, credential_kinds=None):
    attributes = {
        "key": resource_kind_json["key"],
        "nameKey": names.get_key(resource_kind_json["label"]),
        "type": str(type)
    }
    if credential_kinds:
        attributes["credentialKind"] = ",".join(credential_kinds)

    resourcekind_xml = SubElement(parent, "ResourceKind", attrib=attributes, nsmap=ns_map)
    for identifier in resource_kind_json["identifiers"]:
        add_identifier(resourcekind_xml, identifier, names)
    for attribute in resource_kind_json["attributes"]:
        add_attribute(resourcekind_xml, attribute, names)
    for group in resource_kind_json["groups"]:
        add_group(resourcekind_xml, group, names)
    return resourcekind_xml


def add_identifier(parent, identifier_json, names):
    default = identifier_json.get("default")
    if default is None:
        default = ""
    identifier_xml = SubElement(parent, "ResourceIdentifier", attrib={
        "default": str(default),
        "key": identifier_json["key"],
        "nameKey": names.get_key(identifier_json["label"], identifier_json.get("description")),
        "required": str(identifier_json["required"]).lower(),
        "dispOrder": str(identifier_json["display_order"]),
        "enum": str(identifier_json["enum"]).lower(),
        "type": str(identifier_json["type"]),
        "identType": str(identifier_json["ident_type"])
    }, nsmap=ns_map)
    add_enum_values(identifier_xml, identifier_json)
    return identifier_xml


def add_enum_values(parent, identifier_json):
    if "enum_values" in identifier_json:
        for value in identifier_json["enum_values"]:
            SubElement(parent, "enum", attrib={
                "value": str(value),
                "default": str(value == identifier_json.get("default", False)).lower()
            }, nsmap=ns_map)


def add_attribute(parent, attribute_json, names):
    attribute_xml = SubElement(parent, "ResourceAttribute", attrib={
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
        "keyAttribute": str(attribute_json["is_key_attribute"]).lower()
    }, nsmap=ns_map)
    return attribute_xml


def add_group(parent, group_json, names):
    group_xml = SubElement(parent, "ResourceGroup", attrib={
        "key": group_json["key"],
        "nameKey": names.get_key(group_json["label"]),
        "instanced": str(group_json["instanced"]).lower(),
        "instanceRequired": str(group_json["instance_required"]).lower()
    }, nsmap=ns_map)
    for subgroup in group_json.get("groups", []):
        add_group(group_xml, subgroup, names)
    for attribute in group_json.get("attributes", []):
        add_attribute(group_xml, attribute, names)
    return group_xml


def add_units(parent: Element, names):
    unit_definitions = SubElement(parent, "UnitDefinitions", nsmap=ns_map)
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


def add_unit_group(cls, root: Element, names):
    subtypes = set(map(lambda item: item.value._subtype, cls))
    for subtype in subtypes:
        unit_type = SubElement(root, "UnitType", key=cls.__name__ + subtype, nsmap=ns_map)
        for unit in cls:
            if unit.value._subtype == subtype:
                SubElement(unit_type, "Unit", key=unit.value.key, nameKey=names.get_key(unit.value.label),
                           order=str(unit.value._order), conversionFactor=str(unit.value._conversion_factor),
                           nsmap=ns_map)


class _Names:
    def __init__(self):
        self._names = {}
        self.properties = OrderedDict()
        self._count = 0

    def get_key(self, name: str, description: str = None):
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
