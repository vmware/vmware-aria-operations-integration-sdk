import json
import logging
import os

import xml.etree.ElementTree as ET
import xmlschema

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


# TODO: extract this into a class
class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(levelname)s %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def get_describe(path):
    return ET.parse(os.path.join(path, "conf", "describe.xml")).getroot()


def ns(kind):
    return "{http://schemas.vmware.com/vcops/schema}" + kind


def cross_check_metric(collected_metric, resource_kind_element):
    # NOTE: this function will need modifications when we implement validation for groups and instanced groups
    children = resource_kind_element.findall(ns("ResourceAttribute"))
    errors, warnings = 0, 0
    for child in children:
        if not collected_metric["key"] == child.get("key"):
            warnings += 1
            logger.warning(f"Collected metric with key {collected_metric['key']} was not found in describe.xml")

    return errors, warnings


def cross_check_identifiers(collected_identifiers, resource_kind_element):
    described_identifiers = {i.get("key"): i for i in resource_kind_element.findall(ns("ResourceIdentifier"))}

    errors = 0
    warnings = 0
    for identifier in collected_identifiers:
        if identifier["key"] not in described_identifiers.keys():
            warnings += 1
            logger.warning(f"Collected identifier with key {identifier['key']} was not found in describe.xml")
        else:
            if identifier["isPartOfUniqueness"] and described_identifiers[identifier["key"]].get("identType") not in [
                "1", None]:
                warnings += 1
                logger.warning(
                    f"Collected identifier with key {identifier['key']} has isPartOfUniqueness set to true, but identType in describe.xml is not 1")
            elif not identifier["isPartOfUniqueness"] and described_identifiers[identifier["key"]].get(
                    "identType") != "2":
                warnings += 1
                logger.warning(
                    f"Collected identifier with key {identifier['key']} has isPartOfUniqueness set to false, but identType in describe.xml is not 2")

            described_identifiers.pop(identifier["key"])

    for described_identifier in described_identifiers.values():
        if described_identifier.get("required") in ['true', 'True']:
            errors += 1
            logger.error(
                f"Required '{described_identifier.get('key')}' was marked as required in describe.xml, but it was not found in collection.")
        else:
            logger.debug(
                f"'{described_identifier.get('key')}' was declared in describe.xml, but it was not found in collection ")

    return errors, warnings


def cross_check_collection_with_describe(project, request, response, verbose=True):
    user_facing_log = logging.getLogger("user_facing")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(CustomFormatter())
    user_facing_log.addHandler(stream_handler)
    user_facing_log.info("Validating collection results against describe.xml")

    try:
        if verbose:
            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(CustomFormatter())
            logger.addHandler(consoleHandler)

        logger.addHandler(logging.FileHandler(f"{project['path']}/logs/describe_validation.log"))
    except Exception:
        logging.basicConfig(level=logging.CRITICAL + 1)
    path = project["path"]
    results = json.loads(response.text)["result"]
    describe = get_describe(path)
    adapter_kind = get_adapter_kind(describe)
    resource_kinds = get_resource_kinds(describe)

    # store all resourceKind keys in a dictionary for fast lookup
    describe_resources = {resource_kind.get("key"): resource_kind for resource_kind in resource_kinds}

    # check Resource kinds
    errors, warnings = 0, 0
    for resource in results:
        resource_adapter_kind = resource["key"]["adapterKind"]
        resource_kind = resource["key"]["objectKind"]

        # adapter kind validation
        if adapter_kind != resource_adapter_kind:
            warnings += 1
            logger.warning(f"AdapterKind '{adapter_kind}' was expected for object with objectKind '{resource_kind}', "
                           f"but '{resource_adapter_kind}' was found instead")

        # resource kind validation
        if resource_kind not in describe_resources.keys():
            warnings += 1
            # TODO: couple error messages with resource kind and key
            logger.warning(f"No ResourceKind with key '{resource_kind}' was found in the describe.xml")
            logger.info(f"Skipping metric validation for '{resource_kind}'")
        else:
            # metric validation
            described_resource = describe_resources[resource_kind]
            logger.info(f"Validating metrics for {resource_kind}")
            for metric in resource["metrics"]:
                result = cross_check_metric(metric, described_resource)
                errors += result[0]
                warnings += result[1]

            # identifiers validation
            # TODO: small wrapper class that helps count errors and warnings(optional)
            result = cross_check_identifiers(resource["key"]["identifiers"], described_resource)
            errors += result[0]
            warnings += result[1]

    if errors > 0:
        user_facing_log.error(f"Found {errors} errors when validating collection against describe.xml")
    if warnings > 0:
        user_facing_log.warning(f"Found {warnings} minor errors when validating collection against describe.xml")

    if (errors or warnings) > 0:
        user_facing_log.info(f"For detailed logs see '{project['path']}/logs/describe_validation.log'")
    else:
        user_facing_log.info("\u001b[32m Collection matches describe.xml \u001b[0m")


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
