#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import json
from importlib import resources
from json import JSONDecodeError

import openapi_core
from flask import json
from openapi_core.contrib.requests import RequestsOpenAPIRequest, RequestsOpenAPIResponse
from openapi_core.validation.response.validators import ResponseValidator

from vrealize_operations_integration_sdk import api
from vrealize_operations_integration_sdk.validation.result import Result


def validate_api_response(project, request, response):
    result = Result()
    with resources.path(api, "vrops-collector-fwk2-openapi.json") as schema_file:
        with open(schema_file, "r") as schema:
            try:
                json_schema = json.load(schema)
                spec = openapi_core.create_spec(json_schema, validate_spec=True)
                validator = ResponseValidator(spec)
                openapi_request = RequestsOpenAPIRequest(request)
                openapi_response = RequestsOpenAPIResponse(response)
                validation = validator.validate(openapi_request, openapi_response)
                if validation.errors is not None and len(validation.errors) > 0:
                    for error in validation.errors:
                        if "schema_errors" in vars(error):
                            result.with_error(f"schema error: {vars(error)['schema_errors']}")
                        else:
                            result.with_error(error)
            except JSONDecodeError as d:
                result.with_error(f"Returned result is not valid json: '{repr(response.text)}' Error: '{d}'")
    return result
