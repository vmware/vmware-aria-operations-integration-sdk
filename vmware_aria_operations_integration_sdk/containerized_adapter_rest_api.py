#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import json
import os
from typing import Dict
from typing import Tuple

import httpx
from httpx import ReadTimeout
from httpx import Response
from requests import Request

from vmware_aria_operations_integration_sdk.constant import CONNECT_ENDPOINT
from vmware_aria_operations_integration_sdk.describe import Describe
from vmware_aria_operations_integration_sdk.describe import get_adapter_instance
from vmware_aria_operations_integration_sdk.project import Connection
from vmware_aria_operations_integration_sdk.project import Project
from vmware_aria_operations_integration_sdk.timer import timed


@timed
async def get(
    client: httpx.AsyncClient, url: str, headers: Dict
) -> Tuple[Request, Response]:
    # Note: httpx object does not translate nicely into a Request Object (we use this object for validation)
    request = Request(method="GET", url=url, headers=headers)

    response = await client.get(url=url, headers=headers)
    return request, response


@timed
async def post(
    client: httpx.AsyncClient, url: str, json: Dict, headers: Dict
) -> Tuple[Request, Response]:
    # Note: httpx object does not translate nicely into a Request Object (we use this object for validation)
    request = Request(method="POST", url=url, json=json, headers=headers)
    response = await client.post(url=url, json=json, headers=headers)
    return request, response


async def send_post_to_adapter(
    client: httpx.AsyncClient, port: int, connection: Connection, endpoint: str
) -> Tuple[Request, Response, float]:
    try:
        send_cluster_connection_info = endpoint != CONNECT_ENDPOINT
        request, response, elapsed_time = await post(
            client,
            url=f"http://localhost:{port}/{endpoint}",
            json=await get_request_body(port, connection, send_cluster_connection_info),
            headers={"Accept": "application/json"},
        )
    except ReadTimeout as timeout:
        # Translate the error to a standard request response format (for validation purposes)
        timeout_request = timeout.request
        request = Request(
            method=timeout_request.method,
            url=timeout_request.url,
            headers=timeout_request.headers,
        )
        response = Response(408)
        elapsed_time = timeout_request.extensions.get("timeout").get("read")
    return request, response, elapsed_time


async def send_get_to_adapter(
    client: httpx.AsyncClient, port: int, endpoint: str
) -> Tuple[Request, Response, float]:
    try:
        request, response, elapsed_time = await get(
            client,
            url=f"http://localhost:{port}/{endpoint}",
            headers={"Accept": "application/json"},
        )
    except ReadTimeout as timeout:
        # Translate the error to a standard request response format (for validation purposes)
        timeout_request = timeout.request
        request = Request(
            method=timeout_request.method,
            url=timeout_request.url,
            headers=timeout_request.headers,
        )
        response = Response(408)
        elapsed_time = timeout_request.extensions.get("timeout").get("read")
    return request, response, elapsed_time


async def get_request_body(
    port: int, connection: Connection, send_cluster_connection_info: bool = True
) -> Dict:
    describe, resources = await Describe.get(port)
    adapter_instance = get_adapter_instance(describe)
    if adapter_instance is None:
        raise Exception(
            "No adapter instance found in describe. Ensure that an "
            "adapter instance resource kind (with attribute type=7) "
            "exists."
        )

    identifiers = []
    if connection.identifiers is not None:
        for key in connection.identifiers:
            identifiers.append(
                {
                    "key": key,
                    "value": connection.identifiers[key]["value"],
                    "isPartOfUniqueness": connection.identifiers[key][
                        "part_of_uniqueness"
                    ],
                }
            )

    credential_config = {}

    if connection.credential:
        fields = []
        for key in connection.credential:
            if key != "credential_kind_key":
                fields.append(
                    {
                        "key": key,
                        "value": connection.credential[key]["value"],
                        "isPassword": connection.credential[key]["password"],
                    }
                )
        credential_config = {
            "credentialKey": connection.credential["credential_kind_key"],
            "credentialFields": fields,
        }
    suite_api_connection = connection.get_suite_api_connection()
    request_body: Dict[str, object] = {
        "adapterKey": {
            "name": connection.name,
            "adapterKind": describe.get("key"),
            "objectKind": adapter_instance.get("key"),
            "identifiers": identifiers,
        },
        "clusterConnectionInfo": (
            None
            if not send_cluster_connection_info
            else {
                "userName": suite_api_connection.username,
                "password": suite_api_connection.password,
                "hostName": suite_api_connection.hostname,
            }
        ),
        "certificateConfig": {"certificates": connection.certificates or []},
    }
    if connection.custom_collection_number:
        request_body["collectionNumber"] = connection.custom_collection_number
    if connection.custom_collection_window:
        request_body["collectionWindow"] = connection.custom_collection_window
    if credential_config:
        request_body["credentialConfig"] = credential_config

    return request_body


def get_failure_message(response: Response) -> str:
    message = ""
    if not response.is_success:
        message = f"{response.status_code} {response.reason_phrase}"
        if hasattr(response, "text"):
            encoded = response.text.encode("latin1", "backslashreplace").strip(b'"')
            message += "\n" + encoded.decode("unicode-escape")

    elif "errorMessage" in response.text:
        message = json.loads(response.text).get("errorMessage")

    return message
