import json
import logging
import os
import xml.etree.ElementTree as ET

import xmlschema

from common.validation.result import Result

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


def get_describe(path):
    return ET.parse(os.path.join(path, "conf", "describe.xml")).getroot()


def ns(kind):
    return "{http://schemas.vmware.com/vcops/schema}" + kind


def message_format(resource, message):
    resource_kind = resource["key"]["objectKind"]
    # NOTE: Names aren’t guaranteed to be unique, so we should think of a way to further help the user identify the resource
    resource_name = resource["key"]["name"]
    return f"({resource_kind}: {resource_name}) > {message}"


def cross_check_metric(resource, collected_metric, resource_kind_element) -> Result:
    # NOTE: this function will need modifications when we implement validation for groups and instanced groups
    children = resource_kind_element.findall(ns("ResourceAttribute"))
    result = Result()

    match = next(filter(lambda c: c.get("key") == collected_metric["key"], children), None)
    if match is None:
        result.with_warning(
            message_format(
                resource,
                f"Collected metric with key '{collected_metric['key']}' was not found in describe.xml"
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
                    "Collected identifier with key '{identifier['key']}' for resource  was not found in describe.xml"
                )
            )
        else:
            if identifier["isPartOfUniqueness"] and described_identifiers[identifier["key"]].get("identType") not in ["1", None]:
                result.with_warning(
                    message_format(
                        resource,
                        f"Collected identifier with key '{identifier['key']}' has isPartOfUniqueness set to true, but identType in describe.xml is not 1"
                    )
                )
            elif not identifier["isPartOfUniqueness"] and described_identifiers[identifier["key"]].get(
                    "identType") != "2":
                result.with_warning(
                    message_format(
                        resource,
                        f"Collected identifier with key '{identifier['key']}' has isPartOfUniqueness set to false, but identType in describe.xml is not 2"
                    )
                )

            described_identifiers.pop(identifier["key"])

    for described_identifier in described_identifiers.values():
        if described_identifier.get("required") in ['true', 'True']:
            result.with_error(
                message_format(
                    resource,
                    f"Required '{described_identifier.get('key')}' was marked as required in describe.xml, but it was not found in collection."
                )
            )
        else:
            result.with_information(
                message_format(
                    resource,
                    f"'{described_identifier.get('key')}' was declared in describe.xml, but it was not found in collection"
                )
            )

    return result


def cross_check_collection_with_describe(project, request, response):
    path = project["path"]
    results = json.loads(response.text)

    # NOTE: in cases where the adapter crashes (500) results is a string, otherwise is a regular response
    if (type(results) is not dict) or ("result" not in results):
        error = Result()
        error.with_error("No collection result was found")
        return error
    else:
        results = results["result"]

    describe = get_describe(path)
    adapter_kind = get_adapter_kind(describe)
    resource_kinds = get_resource_kinds(describe)

    # store all resourceKind keys in a dictionary for fast lookup
    describe_resource_kinds = {resource_kind.get("key"): resource_kind for resource_kind in resource_kinds}

    # check Resource kinds
    result = Result()
    for resource in results:
        resource_adapter_kind = resource["key"]["adapterKind"]
        resource_kind = resource["key"]["objectKind"]

        # adapter kind validation
        if adapter_kind != resource_adapter_kind:
            result.with_warning(
                message_format(
                    resource,
                    f"AdapterKind '{adapter_kind}' was expected, but '{resource_adapter_kind}' was found instead"
                )
            )

        # resource kind validation
        if resource_kind not in describe_resource_kinds.keys():
            result.with_warning(
                message_format(
                    resource,
                    f"No ResourceKind with key '{resource_kind}' was found in the describe.xml"
                )
            )
            logger.debug(f"Skipping metric validation for '{resource_kind}'")
        else:
            # metric validation
            resource_kind_element = describe_resource_kinds[resource_kind]
            #            logger.info(f"Validating metrics for {resource_kind}")
            for metric in resource["metrics"]:
                result += cross_check_metric(resource, metric, resource_kind_element)

            # identifiers validation
            result += cross_check_identifiers(resource, resource_kind_element)

    return result


def validate_describe(path):
    logger.info("Validating describe.xml")
    # Ensure the describe.xml file is valid NOTE: describeSchema should also enforce duplicates don't exist
    schema = xmlschema.XMLSchema(os.path.join(path, "conf", "describeSchema.xsd"))
    schema.validate(os.path.join(path, "conf", "describe.xml"))


# describe getters
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
