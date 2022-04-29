from vrops.object import Key, Identifier, Object
from vrops.pipe_utils import read_from_pipe
from vrops.suite_api_client import VROpsSuiteApiClient, SuiteApiConnectionParameters


class AdapterInstance(Object):
    def __init__(self, json):
        super().__init__(
            Key(adapter_kind=json["adapter_key"]["adapter_kind"],
                object_kind=json["adapter_key"]["object_kind"],
                name=json["adapter_key"]["name"],
                identifiers=[Identifier(identifier["key"], identifier["value"], identifier["is_part_of_uniqueness"]) for
                             identifier in json["adapter_key"]["identifiers"]]))

        if type(json.get("credential_config")) is dict:
            self.credentials = json["credential_config"]["credential_fields"]
        else:
            self.credentials = None

        if type(json.get("cluster_connection_info")) is dict:
            self.suite_api_client = VROpsSuiteApiClient(SuiteApiConnectionParameters(
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

    @classmethod
    def from_input(cls, infile):
        return cls(read_from_pipe(infile))
