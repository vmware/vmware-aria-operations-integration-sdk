#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import sys
from typing import Optional

from aria.ops.object import Identifier
from aria.ops.object import Key
from aria.ops.object import Object
from aria.ops.pipe_utils import read_from_pipe
from aria.ops.suite_api_client import SuiteApiClient
from aria.ops.suite_api_client import SuiteApiConnectionParameters


class AdapterInstance(Object):  # type: ignore
    def __init__(self, json: dict) -> None:
        adapter_key = json.get("adapter_key", {})
        super().__init__(
            Key(
                adapter_kind=adapter_key.get("adapter_kind"),
                object_kind=adapter_key.get("object_kind"),
                name=adapter_key.get("name"),
                identifiers=[
                    Identifier(
                        identifier.get("key"),
                        identifier.get("value"),
                        identifier.get("is_part_of_uniqueness"),
                    )
                    for identifier in adapter_key.get("identifiers", [])
                ],
            )
        )

        credential_config = json.get("credential_config")
        if type(credential_config) is dict:
            self.credential_type = credential_config.get("credential_key", None)
            self.credentials = {
                credential.get("key"): credential.get("value")
                for credential in credential_config.get("credential_fields", [])
            }
        else:
            self.credential_type = None
            self.credentials = {}

        cluster_connection_info = json.get("cluster_connection_info")
        if type(cluster_connection_info) is dict:
            self.suite_api_client = SuiteApiClient(
                SuiteApiConnectionParameters(
                    username=cluster_connection_info.get("user_name"),
                    password=cluster_connection_info.get("password"),
                    host=cluster_connection_info.get("host_name"),
                )
            )
        else:
            self.suite_api_client = None

        certificate_config = json.get("certificate_config")
        if type(certificate_config) is dict:
            self.certificates = certificate_config.get("certificates", [])
        else:
            self.certificates = []

    def get_credential_type(self) -> Optional[str]:
        """Get the type (key) of credential. This is useful if an adapter supports multiple types of credentials.

        :return: the type of the credential used by this adapter instance, or None if the adapter instance does not have a credential.
        """
        return self.credential_type  # type: ignore[no-any-return]

    def get_credential_value(self, credential_key: str) -> Optional[str]:
        """Retrieve the value of a given credential

        :param credential_key: Key of the credential field
        :return: value associated with the credential field, or None if a credential field with the given key does not exist.
        """
        return self.credentials.get(credential_key)

    @classmethod
    def from_input(cls, infile: str = sys.argv[-2]) -> AdapterInstance:
        # The server always invokes methods with the input file as the second to last argument
        return cls(read_from_pipe(infile))
