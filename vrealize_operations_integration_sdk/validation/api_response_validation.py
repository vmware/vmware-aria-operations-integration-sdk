#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import json
from importlib import resources
from json import JSONDecodeError

import openapi_core
from flask import json
from openapi_core.contrib.requests import RequestsOpenAPIRequest, RequestsOpenAPIResponse
from openapi_core.validation.response import openapi_response_validator

from vrealize_operations_integration_sdk import api
from vrealize_operations_integration_sdk.validation.result import Result


def validate_api_response(project, request, response):
    return _validate_api_response(request, response, "vmware-aria-operations-collector-fwk2.json")


def validate_definition_api_response(project, request, response):
    return _validate_api_response(request, response, "integration-sdk-definition-endpoint.json")


def _validate_api_response(request, response, schema_file):
    result = Result()
    try:
        if not response.is_success:
            result.with_error(f"Unable to validate the response json. The '{request.url}' endpoint "
                              f"response was: {response.status_code} {response.reason_phrase}")
            return result
        with resources.path(api, schema_file) as schema_file:
            with open(schema_file, "r") as schema:
                try:
                    json_schema = json.load(schema)
                    spec = openapi_core.Spec.create(json_schema)
                    openapi_request = RequestsOpenAPIRequest(request)
                    openapi_response = RequestsOpenAPIResponse(response)
                    validation = openapi_response_validator.validate(spec, openapi_request, openapi_response)
                    if validation.errors is not None:
                        for error in validation.errors:
                            if "schema_errors" in vars(error):
                                result.with_error(f"schema error: {vars(error)['schema_errors']}")
                            else:
                                result.with_error(error)
                except JSONDecodeError as d:
                    result.with_error(f"Unable to validate the response json. Returned result is not valid json: "
                                      f"'{repr(response.text)}' Error: '{d}'")
    except Exception as e:
        result.with_error(f"Unable to validate the response json: '{e}'")

    return result
