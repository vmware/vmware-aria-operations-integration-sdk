#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import json
import os

import httpx
from httpx import ReadTimeout, Response
from requests import Request

from vmware_aria_operations_integration_sdk.src.config import get_config_value
from vmware_aria_operations_integration_sdk.src.constant import DEFAULT_PORT
from vmware_aria_operations_integration_sdk.src.describe import get_adapter_instance, Describe
from vmware_aria_operations_integration_sdk.src.timer import timed


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
                                                     json=await get_request_body(project, connection),
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


async def get_request_body(project, connection):
    describe, resources = await Describe.get()
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

    hostname = get_config_value("suite_api_hostname", "string", os.path.join(project.path, "config.json"))
    username = get_config_value("suite_api_username", "string", os.path.join(project.path, "config.json"))
    password = get_config_value("suite_api_password", "string", os.path.join(project.path, "config.json"))

    request_body = {
        "adapterKey": {
            "name": connection.name,
            "adapterKind": describe.get("key"),
            "objectKind": adapter_instance.get("key"),
            "identifiers": identifiers,
        },
        "clusterConnectionInfo": {
            "userName": username,
            "password": password,
            "hostName": hostname,
        },
        "certificateConfig": {
            "certificates": connection.certificates or []
        }
    }
    if credential_config:
        request_body["credentialConfig"] = credential_config

    return request_body


def get_failure_message(response):
    message = ""
    if not response.is_success:
        message = f"{response.status_code} {response.reason_phrase}"
        if hasattr(response, "text"):
            encoded = response.text.encode('latin1', 'backslashreplace').strip(b'"')
            message += "\n" + encoded.decode('unicode-escape')

    elif "errorMessage" in response.text:
        message = json.loads(response.text).get('errorMessage')

    return message
