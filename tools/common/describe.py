import json
import logging
import os

import xml.etree.ElementTree as ET
import xmlschema

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = logging.StreamHandler()
logger.addHandler(consoleHandler)


def get_describe(path):
    return ET.parse(os.path.join(path, "conf", "describe.xml")).getroot()


def ns(kind):
    return "{http://schemas.vmware.com/vcops/schema}" + kind


def cross_check_metric(metric, resource):
    # NOTE: this function will need modifications when we implement validation for groups and instanced groups
    children = resource.findall(ns("ResourceAttribute"))

    for child in children:
        if metric["key"] == child.get("key"):
            return True

    return False


def cross_check_identifiers(identifiers, resource):
    # NOTE: identifiers have to be checked as a group, since they can be dependent on one another
    described_indentifiers = {i.get("key"): i for i in resource.findall(ns("ResourceIdentifier"))}

    for identifier in  identifiers:
        if  identifier["key"] not in described_indentifiers.keys():
            if identifier["isPartOfUniqueness"]:
                logger.error(f"Collected indetifier with key {identifier['key']} should be defined in the describe.xml")
            else:
                logger.warning(f"Collected indetifier with key {identifier['key']} was not found in describe.xml")
        else:
            described_indentifiers.pop(identifier["key"])

    for described_indentifier in described_indentifiers.values():
        if described_indentifier.get("required") in ['true', 'True']:
            logger.error(f"Required '{described_indentifier.get('key')}' was declared in describe.xml, but it was not found in collection ")
        else:
            logger.warning(f"'{described_indentifier.get('key')}' was declared in describe.xml, but it was not found in collection ")



def cross_check_collection_with_describe(project, request, response):
    path = project["path"]
    results = json.loads(response.text)["result"]
    describe = get_describe(path)
    adapter_kind = get_adapter_kind(describe)
    resource_kinds = get_resource_kinds(describe)

    # store all resourceKind keys in a dictionary for fast lookup
    describe_resources = {resource_kind.get("key"): resource_kind for resource_kind in resource_kinds}

    # check Resource kinds
    for resource in results:
        resource_adapter_kind = resource["key"]["adapterKind"]
        resource_kind = resource["key"]["objectKind"]

        # adapter kind validation
        if adapter_kind != resource_adapter_kind:
            logger.warning(f"AdapterKind '{adapter_kind}' was expected for object with objectKind '{resource_kind}', "
                           f"but '{resource_adapter_kind}' was found instead")

        # resource kind validation
        if resource_kind not in describe_resources.keys():
            logger.warning(f"No ResourceKind with key '{resource_kind}' was found in the describe.xml")
            logger.info(f"Skipping metric validation for '{resource_kind}'")
        else:
            # metric validation
            logger.info(f"Validating metrics for {resource_kind}")
            for metric in resource["metrics"]:
                if not cross_check_metric(metric, describe_resources[resource_kind]):
                    logger.warning(f"Collected metric with key {metric['key']} was not found in describe.xml")

            # identifiers validation
            cross_check_identifiers(resource["key"]["identifiers"], describe_resources[resource_kind])



def validate_describe(path):
    logger.info("Validating describe.xml")
    # Ensure the describe.xml file is valid NOTE: describeSchema should also enforce dupplicates don't exist
    schema = xmlschema.XMLSchema(os.path.join(path, 'conf', 'describeSchema.xsd'))
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
