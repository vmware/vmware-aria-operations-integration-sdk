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
    children = resource.findall(ns("ResourceAttribute"))

    for child in children:
        if metric["key"] == child.get("key"):
            return True

    return False


def cross_check_collection_with_describe(path, response):
    results = json.loads(response.text)["result"]
    describe = get_describe(path)
    adapter_kind = get_adapter_kind(describe)
    resource_kinds = get_resource_kinds(describe)

    # check Resource kinds
    for resource in results:
        resource_adapter_kind = resource["key"]["adapterKind"]
        resource_kind = resource["key"]["objectKind"]

        if adapter_kind != resource_adapter_kind:
            logger.warning(f"AdapterKind {adapter_kind} was expected for object with objectKind {resource_kind}, "
                           f"but {resource_adapter_kind} was found instead")

        element = list(e for e in resource_kinds if e.get("key") == resource_kind)

        if not element:
            logger.warning(f"No ResourceKind with key {resource_kind} was found in the describe.xml")
            logger.info(f"Skipping metric validation for {resource_kind}")
        else:
            element = element.pop()
            for metric in resource["metrics"]:
                if not cross_check_metric(metric, element):
                    logger.warning(f"collected metric with key {metric['key']} was not found in describe.xml")
                    logger.info(f"Add ResourceAttribute with key: {metric['key']} to describe.xml")


def validate_describe(path):
    logger.info("Validating describe.xml")
    # Ensure the describe.xml file is valid NOTE: describeSchema should also enforce dupplicates don't exist
    schema = xmlschema.XMLSchema(os.path.join(path, 'conf/describeSchema.xsd'))
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
