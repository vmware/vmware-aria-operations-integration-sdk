#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import sys
from typing import Dict
from typing import Optional

from aria.ops.certificate_info import CertificateInfo
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
        self.certificates: list[CertificateInfo] = []
        if type(certificate_config) is dict:
            self.certificates = [
                CertificateInfo(cert)
                for cert in certificate_config.get("certificates", [])
            ]

        self.collection_number: Optional[int] = json.get("collection_number", None)
        self.collection_window: Optional[Dict] = json.get("collection_window", None)

    def get_suite_api_client(self) -> Optional[SuiteApiClient]:
        """
        Gets an authenticated Suite API Client. Note that Suite API calls can only be
        made from the 'collect' endpoint. Returns 'None' when called from 'test' and
        'get_endpoints'.

        Returns:
            Authenticated SuiteApiClient, or None
        """
        return self.suite_api_client

    def get_certificates(self) -> list[CertificateInfo]:
        """
        Gets a list of all certificates that have been validated by a CA or manually
        accepted by a user.

        Returns:
            A list of certificates for verifying SSL connections.
        """
        return self.certificates

    def get_collection_number(self) -> Optional[int]:
        """
        Gets the current collection number, starting from 0.
        Returns 'None' when called from 'test' and 'get_endpoints'.

        Returns:
            The current collection number
        """
        return self.collection_number

    def get_collection_window(self) -> Optional[Dict]:
        """Gets the window for the current collection.

         In some cases, it is useful to have a start and end time for collection. The
         start_time and end_time will be modified each collection such that each
         collection's end_time will be the next collection's start_time. Thus, the
         window can be treated as either the interval `(start_time, end_time]` or
         `[start_time, end_time)`, so long as each collection uses the same convention,
         there will be no overlaps or missing times. (Note that restarting the adapter
         instance will reset the time window. In general, this will cause overlap
         and/or missing times when restarts occur for any reason).

         Times are provided in milliseconds since the Epoch.

        Returns:
            A dictionary with two keys: 'start_time' and 'end_time'. On the first
            collection, 'start_time' will be set to '0'. On calls to 'test' and
            'get_endpoints', this will be 'None'.
        """
        return self.collection_window

    def get_credential_type(self) -> Optional[str]:
        """Get the type (key) of credential. This is useful if an adapter supports multiple types of credentials.

        Returns:
            the type of the credential used by this adapter instance, or None if the adapter instance does not have a credential.
        """
        return self.credential_type  # type: ignore[no-any-return]

    def get_credential_value(self, credential_key: str) -> Optional[str]:
        """Retrieve the value of a given credential

        Args:
            credential_key (str): Key of the credential field

        Returns:
            value associated with the credential field, or None if a credential field with the given key does not exist.
        """
        return self.credentials.get(credential_key)

    @classmethod
    def from_input(cls, infile: str = sys.argv[-2]) -> AdapterInstance:
        # The server always invokes methods with the input file as the second to last argument
        return cls(read_from_pipe(infile))
