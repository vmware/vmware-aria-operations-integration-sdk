#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
from json import JSONDecodeError

import xmlschema

from vrealize_operations_integration_sdk.describe import get_describe, get_adapter_kind, get_resource_kinds, ns, \
    is_true
from vrealize_operations_integration_sdk.validation.result import Result

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


def message_format(resource, message):
    resource_kind = resource["key"]["objectKind"]
    # NOTE: Names aren’t guaranteed to be unique, so we should think of a way to further help the user identify the resource
    resource_name = resource["key"]["name"]
    return f"({resource_kind}: {resource_name}) > {message}"


def cross_check_attribute(resource, collected_metric, attribute_type, key_, element) -> Result:
    result = Result()
    key, _, remaining_key = key_.partition("|")
    if remaining_key != "":
        child_type = "ResourceGroup"
    else:
        child_type = "ResourceAttribute"

    key, _, instance = key.partition(":")
    instanced = (instance != "")
    children = element.findall(ns(child_type))
    match = next(filter(lambda c: c.get("key") == key, children), None)

    if match is None:
        result.with_warning(
            message_format(
                resource,
                f"{attribute_type.capitalize()} '{collected_metric['key']}' is not defined in describe.xml. Could not "
                f"find {child_type} '{key}'."
            )
        )
        return result

    if child_type == "ResourceGroup":

        if is_true(match, "instanced") and is_true(match, "instanceRequired"):
            if not instanced:
                result.with_warning(
                    message_format(
                        resource,
                        f"{attribute_type.capitalize()} '{collected_metric['key']}' has an invalid key. It contains "
                        f"non-instanced group '{key}', but that group is defined to require instances in describe.xml."
                    )
                )
        if instanced and not is_true(match, "instanced"):
            result.with_warning(
                message_format(
                    resource,
                    f"{attribute_type.capitalize()} '{collected_metric['key']}' has an invalid key. It contains "
                    f"instanced group '{key}', but that group is not defined to allow instances in describe.xml."
                )
            )
        result += cross_check_attribute(resource, collected_metric, attribute_type, remaining_key, match)
        return result

    # attribute validation cases
    if is_true(match, "isProperty") != (attribute_type == "property"):
        describe_attribute_type = "property" if is_true(match, "isProperty") else "metric"
        result.with_warning(
            message_format(
                resource,
                f"{attribute_type.capitalize()} '{collected_metric['key']}' has a mismatched type. It was returned as a"
                f" {attribute_type}, but the attribute is defined as a {describe_attribute_type} in describe.xml."
            )
        )
    # TODO: Can we modify the describeSchema.xsd file to disallow this case?
    if (match.get("type", "float") == "string") and not is_true(match, "isProperty"):
        result.with_error(
            message_format(
                resource,
                f"{attribute_type.capitalize()} '{collected_metric['key']}' has an invalid data type in describe.xml. "
                f"Only properties can have type 'string'."
            )
        )

    if ("stringValue" in collected_metric) and (match.get("dataType", "float") != "string"):
        result.with_error(
            message_format(
                resource,
                f"{attribute_type.capitalize()} '{collected_metric['key']}' has an invalid data type. A string value "
                f"was returned in the collection, but the attribute is defined as numeric in describe.xml."
            )
        )
    if ("numberValue" in collected_metric) and (match.get("type", "float").lower() == "string"):
        result.with_error(
            message_format(
                resource,
                f"{attribute_type.capitalize()} '{collected_metric['key']}' has an invalid data type. A numeric value "
                f"was returned in the collection, but the attribute type is 'string' in describe.xml."
            )
        )

    return result


def cross_check_identifiers(resource, resource_kind_element) -> Result:
    collected_identifiers = resource["key"]["identifiers"]
    described_identifiers = {i.get("key"): i for i in resource_kind_element.findall(ns("ResourceIdentifier"))}

    result = Result()
    for identifier in collected_identifiers:
        if identifier["key"] not in described_identifiers.keys():
            result.with_warning(
                message_format(
                    resource,
                    f"Identifier '{identifier['key']}' is present on this resource, but is not defined in describe.xml."
                )
            )
        else:
            if identifier["isPartOfUniqueness"] and \
                    described_identifiers[identifier["key"]].get("identType", "1") != "1":
                result.with_error(
                    message_format(
                        resource,
                        f"Identifier '{identifier['key']}' uniqueness mismatch. 'isPartOfUniqueness' is set to true "
                        f"in the collection, which is inconsistent with 'identType=\"2\" in describe.xml."
                    )
                )
            elif not identifier["isPartOfUniqueness"] and described_identifiers[identifier["key"]].get(
                    "identType", "1") != "2":
                result.with_error(
                    message_format(
                        resource,
                        f"Identifier '{identifier['key']}' uniqueness mismatch. 'isPartOfUniqueness' set to false in "
                        f"the collection, which is inconsistent with 'identType=\"1\"' in describe.xml."
                    )
                )

            described_identifiers.pop(identifier["key"])

    for described_identifier in described_identifiers.values():
        if is_true(described_identifier, "required", default="true"):
            result.with_error(
                message_format(
                    resource,
                    f"Identifier '{described_identifier.get('key')}' is required in describe.xml, but it was not "
                    f"found on this resource."
                )
            )
        else:
            result.with_information(
                message_format(
                    resource,
                    f"Identifier '{described_identifier.get('key')}' is optional in describe.xml, and was not found "
                    f"on this resource."
                )
            )

    return result


def cross_check_collection_with_describe(project, request, response):
    result = Result()
    try:
        if not response.is_success:
            result.with_error(f"Unable to cross check collection against describe.xml. The '{request.url}' endpoint "
                              f"response was: {response.status_code} {response.reason_phrase}")
            return result
        path = project.path
        results = json.loads(response.text)

        # NOTE: in cases where the adapter crashes (500) results is a string, otherwise is a regular response
        if (type(results) is not dict) or ("result" not in results):
            error = Result()
            error.with_error("No collection result was found.")
            return error
        else:
            results = results["result"]

        describe = get_describe(path)
        adapter_kind = get_adapter_kind(describe)
        resource_kinds = get_resource_kinds(describe)

        # store all resourceKind keys in a dictionary for fast lookup
        describe_resource_kinds = {resource_kind.get("key"): resource_kind for resource_kind in resource_kinds}

        # check Resource kinds
        for resource in results:
            resource_adapter_kind = resource["key"]["adapterKind"]
            resource_kind = resource["key"]["objectKind"]

            # adapter kind validation
            if adapter_kind != resource_adapter_kind:
                result.with_warning(
                    message_format(
                        resource,
                        f"AdapterKind '{adapter_kind}' was expected, but '{resource_adapter_kind}' was found instead. "
                    )
                )

            # resource kind validation
            if resource_kind not in describe_resource_kinds.keys():
                result.with_warning(
                    message_format(
                        resource,
                        f"ResourceKind '{resource_kind}' was not found in describe.xml. "
                    )
                )
                logger.debug(f"Skipping metric validation for '{resource_kind}'. ")
            else:
                # metric validation
                resource_kind_element = describe_resource_kinds[resource_kind]
                #            logger.info(f"Validating metrics for {resource_kind}")
                for metric in resource["metrics"]:
                    result += cross_check_attribute(resource, metric, "metric", metric["key"], resource_kind_element)
                for prop in resource["properties"]:
                    result += cross_check_attribute(resource, prop, "property", prop["key"], resource_kind_element)

                # identifiers validation
                result += cross_check_identifiers(resource, resource_kind_element)

    except JSONDecodeError as d:
        result.with_error(f"Unable to cross check collection against describe.xml. Returned result is not valid json: "
                          f"'{repr(response.text)}' Error: '{d}'")
    except Exception as e:
        result.with_error(f"Unable to cross check collection against describe.xml: '{e}'")

    return result


def validate_describe(path):
    logger.info("Validating describe.xml")
    # TODO: Ensure the describe.xml file is valid NOTE: describeSchema should also enforce duplicates don't exist
    schema = xmlschema.XMLSchema(os.path.join(path, "conf", "describeSchema.xsd"))
    schema.validate(os.path.join(path, "conf", "describe.xml"))
