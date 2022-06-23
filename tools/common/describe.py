import json
import logging
import os

import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = logging.StreamHandler()
logger.addHandler(consoleHandler)


def get_describe(path):
    return ET.parse(os.path.join(path, "conf", "describe.xml")).getroot()


def ns(kind):
    return "{http://schemas.vmware.com/vcops/schema}" + kind


def validate_resource_kinds(adapter_kind_key, resource_kinds, response):
    """ Ensures that each Object in the response has a matching  ResourceKind in the describe.xml

    There can be multiple instances of the same resource kind in the response

    A resource can be present in in the describe xml, but not in the response, in which case we should make note
    of the resource either missing from collection, or not having the right key.

    If a Resource is present in the collection result, but not in the describe.xml, then we consider that an error

    ResourceKinds must have unique keys and nameKeys

    All objects should have the same AdapterKind

    :param adapter_kind_key:
    :param resource_kinds:
    :param response:
    :return:
    """
    logger.info("Validating ResourceKinds")

    # Validate describe.xml portion of the resources, by making sure they have unique keys and nameKeys
    copy = resource_kinds.copy()
    for resource in copy:
        name_key = resource.get("nameKey")
        key = resource.get("Key")
        name_key_matches = list(filter(lambda r: r.get("nameKey") == name_key, resource_kinds))
        key_matches = list(filter(lambda r: r.get("key") == key, resource_kinds))

        # NOTE: since we are iterating through the list, we are going to see this message appear as many times as the
        # repeated resource
        # NOTE: Maybe we write a helper function that checks for duplicate keys
        if len(name_key_matches) > 1:
            logger.warning(f"Found {len(name_key_matches)} instances of {name_key} as a nameKey, when nameKey should "
                           f"be unique")

        if len(key_matches) > 1:  # Check duplicate keys
            logger.warning(f"Found {len(key_matches)} instances of {key} as a Key, when Key should be unique")

        copy.remove(resource)

    # Validate each json object against the describe.xml
    for _object in response:
        object_adapter_kind_key = _object["key"]["adapterKind"]
        # NOTE: does the json validation ensure that this keys are present or should we except an error here? Yes it
        # does for customers using the SDK, but not for customers writing their own abominations
        object_kind_key = _object["key"]["objectKind"]

        if adapter_kind_key != object_adapter_kind_key:
            logger.warning(f"AdapterKind {adapter_kind_key} was expected for object with objectKind {object_kind_key}, "
                           f"but {object_adapter_kind_key} was found instead")

        # find any ResourceKind with a matching Key
        matches = list(filter(lambda e: e.get("key") == object_kind_key, resource_kinds))
        num_matches = len(matches)

        if num_matches == 1:
            # good stuff the resource kind was found in the describe.xml
            logger.info(f"{object_kind_key} is valid")
        elif num_matches > 1:
            # element and tell the user about them being duplicates
            logger.error(f"There was {num_matches} ResourceKinds with the key {object_kind_key}")
        else:
            # nothing found means that the object from the response is not present in the describe.xml
            logger.warning(f"No ResourceKind with key {adapter_kind_key} was found in the describe.xml")


def validate_resource_identifiers(resource_kinds, response):
    """

     An Identifier that isPartOfUniqueness, should be unique

     If a ResourceIdentifier is present in collection, but not in the describe.xml then we should report it/ consider
     it an error

    A ResourceKind should not have two of the same identifier
    ResourceIdentifiers have unique nameKey, dispOrder, and key


    :param resource_kinds:
    :param response:
    :return:
    """

    # NOTE: If a ResourceKind has no identifier, should we report it?

    # First we validate the individual requirements for the describe.xml
    for resource in resource_kinds:
        identifiers = get_identifiers(resource)
        resource_key = resource.get("key")

        duplicates = {}
        logger.info(f"Validating identifiers for ResourceKind: {resource_key}")
        for identifier in identifiers:
            name_key = identifier.get("nameKey")
            key = identifier.get("key")
            disp_order = identifier.get("dispOrder")

            # TODO: improve logic
            if name_key in duplicates:
                duplicate = duplicates[f"{name_key}"]

                duplicate["count"] = duplicate["count"] + 1
            else:
                duplicates[f"{name_key}"] = {
                    "count": 1,
                    "key": name_key
                }

            if key in duplicates:
                duplicate = duplicates[f"{key}"]

                duplicate["count"] = duplicate["count"] + 1
            else:
                duplicates[f"{key}"] = {
                    "count": 1,
                    "key": [key],
                }

            if disp_order in duplicates:
                duplicate = duplicates[f"{disp_order}"]

                duplicate["count"] = duplicate["count"] + 1
            else:
                duplicates[f"{disp_order}"] = {
                    "count": 1,
                    "key": key
                }

        for key, value in duplicates.items():
            if value["count"] > 1:
                logger.info(f"duplicated attribute {value['key']} in {resource.get('key')}")

        # Iterate thorough dictionary and check for duplicates
        # if duplicate["count"] > 1:
        #     logger.info(f"There where {duplicate['count']} instances of attribute {duplicate['key']}")

    # TODO: check for uniqueness in every key

    # Cross validate the JSON with teh describe.xml
    # for _object in response:
    #     identifiers = _object["key"]["identifiers"]
    #
    #     for identifier in identifiers:
    #
    #


def validate_describe(response, project):
    """ Validate the adapter response against the describe.xml



    :param response: A JSON object generated by the adapter as the result of a request
    :param project: Metadata about the project being tested (we need this to get the describe.xml)
    :return: None
    """
    logger.info("Validating collection response against describe.xml")
    logger.info("################################################")
    results = json.loads(response.text)["result"]
    describe = get_describe(project["path"])
    adapter_kind = get_adapter_kind(describe)
    resource_kinds = get_resource_kinds(describe)

    # check Resource kinds
    validate_resource_kinds(adapter_kind, resource_kinds, results)

    # NOTE: We need the ResourceKind to validate parts of the identifiers
    validate_resource_identifiers(resource_kinds, results)

    # TODO: check Object Identifiers


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
