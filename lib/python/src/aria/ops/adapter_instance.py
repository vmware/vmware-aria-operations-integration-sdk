#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import sys

from aria.ops.object import Key, Identifier, Object
from aria.ops.pipe_utils import read_from_pipe
from aria.ops.suite_api_client import SuiteApiClient, SuiteApiConnectionParameters


class AdapterInstance(Object):
    def __init__(self, json):
        super().__init__(
            Key(adapter_kind=json["adapter_key"]["adapter_kind"],
                object_kind=json["adapter_key"]["object_kind"],
                name=json["adapter_key"]["name"],
                identifiers=[Identifier(identifier["key"], identifier["value"], identifier["is_part_of_uniqueness"]) for
                             identifier in json["adapter_key"]["identifiers"]]))

        if type(json.get("credential_config")) is dict:
            self.credential_type = json["credential_config"]["credentialKey"]
            self.credentials = {credential.get("key"): credential.get("value")
                                for credential in json["credential_config"]["credential_fields"]}
        else:
            self.credential_type = None
            self.credentials = {}

        if type(json.get("cluster_connection_info")) is dict:
            self.suite_api_client = SuiteApiClient(SuiteApiConnectionParameters(
                username=json["cluster_connection_info"]["user_name"],
                password=json["cluster_connection_info"]["password"],
                host=json["cluster_connection_info"]["host_name"]
            ))
        else:
            self.suite_api_client = None
        if type(json.get("certificate_config")) is dict:
            self.certificates = json["certificate_config"]["certificates"]
        else:
            self.certificates = []

    def get_credential_type(self):
        """ Get the type (key) of credential. This is useful if an adapter supports multiple types of credentials.

        :return: the type of the credential used by this adapter instance, or None if the adapter instance does not have a credential.
        """
        return self.credential_type

    def get_credential_value(self, credential_key):
        """ Retrieve the value of a given credential

        :param credential_key: Key of the credential field
        :return: value associated with the credential field, or None if a credential field with the given key does not exist.
        """
        return self.credentials.get(credential_key)

    @classmethod
    def from_input(cls, infile=sys.argv[-2]):
        # The server always invokes methods with the input file as the second to last argument
        return cls(read_from_pipe(infile))
