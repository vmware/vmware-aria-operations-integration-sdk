#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import json
from json import JSONDecodeError

import validators
from httpx import Response
from requests import Request
from validators import ValidationFailure

from vmware_aria_operations_integration_sdk.project import Project
from vmware_aria_operations_integration_sdk.validation.result import Result


def validate_endpoint(endpoint: str) -> Result:
    result = Result()
    url_validation_result = validators.url(endpoint)
    if "://" not in endpoint:
        result.with_error(
            f"Endpoint '{endpoint}' must include a protocol. Supported protocols are: ['https']."
        )
    elif not endpoint.startswith("https://"):
        result.with_error(f"Endpoint '{endpoint}' protocol must be 'https'.")
    elif type(url_validation_result) is ValidationFailure:
        result.with_error(f"Endpoint '{endpoint}' is not a valid URL.")

    if not (result.error_count or result.warning_count):
        result.with_success(f"{endpoint} is a valid URL.")
    return result


def validate_endpoint_urls(
    project: Project, request: Request, response: Response
) -> Result:
    result = Result()
    try:
        if not response.is_success:
            result.with_error(
                f"Unable to validate EndpointURLs content. The '{request.url}' endpoint response was: "
                f"{response.status_code} {response.reason_phrase}"
            )
            return result
        results = json.loads(response.text)
        endpoints = results.get("endpointUrls", [])
        for endpoint in endpoints:
            result += validate_endpoint(endpoint)

    except JSONDecodeError as d:
        result.with_error(
            f"Unable to validate EndpointURLs content. Returned result is not valid json: "
            f"'{repr(response.text)}' Error: '{d}'"
        )
    except Exception as e:
        result.with_error(f"Unable to validate EndpointURL content: '{e}'")

    return result
