#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import json
from importlib import resources
from json import JSONDecodeError

import openapi_core
from httpx import Response
from openapi_core.contrib.requests import RequestsOpenAPIRequest
from openapi_core.contrib.requests import RequestsOpenAPIResponse
from openapi_core.validation.response import openapi_response_validator
from requests import Request

import vmware_aria_operations_integration_sdk.api as api
from vmware_aria_operations_integration_sdk.containerized_adapter_rest_api import (
    get_failure_message,
)
from vmware_aria_operations_integration_sdk.project import Project
from vmware_aria_operations_integration_sdk.validation.result import Result


def validate_api_response(
    project: Project, request: Request, response: Response
) -> Result:
    return _validate_api_response(
        request, response, "vmware-aria-operations-collector-fwk2.json"
    )


def validate_definition_api_response(
    project: Project, request: Request, response: Response
) -> Result:
    if response.status_code == 204:
        return Result()
    return _validate_api_response(
        request, response, "integration-sdk-definition-endpoint.json"
    )


def _validate_api_response(
    request: Request, response: Response, schema_filename: str
) -> Result:
    result = Result()
    try:
        if not response.is_success:
            result.with_error(
                f"Unable to validate the response json. The '{request.url}' endpoint "
                f"response was: \n {get_failure_message(response)}"
            )
            return result
        with resources.path(api, schema_filename) as schema_file:
            with open(schema_file, "r") as schema:
                try:
                    json_schema = json.load(schema)
                    spec = openapi_core.Spec.create(json_schema)
                    openapi_request = RequestsOpenAPIRequest(request)
                    openapi_response = RequestsOpenAPIResponse(response)
                    validation = openapi_response_validator.validate(
                        spec, openapi_request, openapi_response
                    )
                    if validation.errors is not None:
                        for error in validation.errors:
                            if "schema_errors" in vars(error):
                                result.with_error(
                                    f"schema error: {vars(error)['schema_errors']}"
                                )
                            else:
                                result.with_error(error)
                except JSONDecodeError as d:
                    result.with_error(
                        f"Unable to validate the response json. Returned result is not valid json: "
                        f"'{repr(response.text)}' Error: '{d}'"
                    )
    except Exception as e:
        result.with_error(f"Unable to validate the response json: '{e}'")

    return result
