#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import httpx
from httpx import ReadTimeout, Response
from requests import Request

from vrealize_operations_integration_sdk.constant import DEFAULT_PORT
from vrealize_operations_integration_sdk.describe import get_describe, get_adapter_instance
from vrealize_operations_integration_sdk.timer import timed


@timed
async def get(client: httpx.AsyncClient, url, headers):
    # Note: httpx object does not translate nicely into a Request Object (we use this object for validation)
    request = Request(method="GET",
                      url=url,
                      headers=headers)

    response = await client.get(url=url, headers=headers)
    return request, response


@timed
async def post(client, url, json, headers):
    # Note: httpx object does not translate nicely into a Request Object (we use this object for validation)
    request = Request(method="POST", url=url,
                      json=json,
                      headers=headers)
    response = await client.post(url=url, json=json, headers=headers)
    return request, response


async def send_post_to_adapter(client, project, connection, endpoint):
    try:
        request, response, elapsed_time = await post(client, url=f"http://localhost:{DEFAULT_PORT}/{endpoint}",
                                                     json=get_request_body(project, connection),
                                                     headers={"Accept": "application/json"})
    except ReadTimeout as timeout:
        # Translate the error to a standard request response format (for validation purposes)
        timeout_request = timeout.request
        request = Request(method=timeout_request.method, url=timeout_request.url,
                          headers=timeout_request.headers)
        response = Response(408)
        elapsed_time = timeout_request.extensions.get("timeout").get("read")
    return request, response, elapsed_time


async def send_get_to_adapter(client, endpoint):
    try:
        request, response, elapsed_time = await get(client,
                                                    url=f"http://localhost:{DEFAULT_PORT}/{endpoint}",
                                                    headers={"Accept": "application/json"}
                                                    )
    except ReadTimeout as timeout:
        # Translate the error to a standard request response format (for validation purposes)
        timeout_request = timeout.request
        request = Request(method=timeout_request.method, url=timeout_request.url,
                          headers=timeout_request.headers)
        response = Response(408)
        elapsed_time = timeout_request.extensions.get("timeout").get("read")
    return request, response, elapsed_time


def get_request_body(project, connection):
    describe = get_describe(project.path)
    adapter_instance = get_adapter_instance(describe)

    identifiers = []
    if connection.identifiers is not None:
        for key in connection.identifiers:
            identifiers.append({
                "key": key,
                "value": connection.identifiers[key]["value"],
                "isPartOfUniqueness": connection.identifiers[key]["part_of_uniqueness"]
            })

    credential_config = {}

    if connection.credential:
        fields = []
        for key in connection.credential:
            if key != "credential_kind_key":
                fields.append({
                    "key": key,
                    "value": connection.credential[key]["value"],
                    "isPassword": connection.credential[key]["password"]
                })
        credential_config = {
            "credentialKey": connection.credential["credential_kind_key"],
            "credentialFields": fields,
        }

    request_body = {
        "adapterKey": {
            "name": connection.name,
            "adapterKind": describe.get("key"),
            "objectKind": adapter_instance.get("key"),
            "identifiers": identifiers,
        },
        "clusterConnectionInfo": {
            "userName": "string",
            "password": "string",
            "hostName": "string"
        },
        "certificateConfig": {
            "certificates": connection.certificates or []
        }
    }
    if credential_config:
        request_body["credentialConfig"] = credential_config

    return request_body
