from common.constant import DEFAULT_PORT
from common.describe import get_describe, get_adapter_instance
from common.timer import timed
import requests


@timed
def get(url, headers):
    request = requests.models.Request(method="GET",
                                      url=url,
                                      headers=headers)
    response = requests.get(url=url, headers=headers)
    return request, response


@timed
def post(url, json, headers):
    request = requests.models.Request(method="POST", url=url,
                                      json=json,
                                      headers=headers)
    response = requests.post(url=url, json=json, headers=headers)
    return request, response


def send_post_to_adapter(project, connection, endpoint):
    return post(url=f"http://localhost:{DEFAULT_PORT}/{endpoint}",
                json=get_request_body(project, connection),
                headers={"Accept": "application/json"})


def send_get_to_adapter(endpoint):
    return get(
        url=f"http://localhost:{DEFAULT_PORT}/{endpoint}",
        headers={"Accept": "application/json"}
    )


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
            "certificates": []
        }
    }
    if credential_config:
        request_body["credentialConfig"] = credential_config

    return request_body
