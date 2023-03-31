#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import json
import logging
import os
from json import JSONDecodeError

from httpx import Response
from requests import Request

from vmware_aria_operations_integration_sdk.describe import Describe
from vmware_aria_operations_integration_sdk.describe import json_to_xml
from vmware_aria_operations_integration_sdk.logging_format import CustomFormatter
from vmware_aria_operations_integration_sdk.logging_format import PTKHandler
from vmware_aria_operations_integration_sdk.project import Project
from vmware_aria_operations_integration_sdk.validation.describe_checks import (
    validate_describe,
)
from vmware_aria_operations_integration_sdk.validation.result import Result

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = PTKHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)


def validate_adapter_definition(
    project: Project, request: Request, response: Response
) -> Result:
    result = Result()
    if not response.is_success:
        # Failure case is already handled in first validator that AdapterDefinitionBundle calls
        return result
    if response.status_code == 204:
        result.with_warning(
            "No adapter description was returned by the adapter. Note: This is the expected result \n"
            "when using a 'describe.xml' file rather than implementing the adapterDefinition endpoint\n"
            "in the adapter."
        )
        return result
    try:
        ad = json.loads(response.text)
        describe, names = json_to_xml(ad)
        Describe.initialize(project.path, None)
        Describe.merge_xml_fragments(describe, names)

        validate_describe(project.path, describe)
    except JSONDecodeError as d:
        result.with_error(
            f"Unable to validate the response json. Returned result is not valid json: "
            f"'{repr(response.text)}' Error: '{d}'"
        )
    except Exception as e:
        result.with_error(f"Unable to validate the response json: '{e}'")

    if not (result.error_count or result.warning_count):
        result.with_success("Json response from adapter validates against the schema.")

    return result
