from vrops.object import Key, Identifier, Object
from vrops.pipe_utils import read_from_pipe
from vrops.suite_api_client import VROpsSuiteApiClient


class AdapterInstance(Object):
    def __init__(self, json):
        super().__init__(
            Key(adapter_kind=json["adapter_key"]["adapter_kind"],
                object_kind=json["adapter_key"]["object_kind"],
                name=json["adapter_key"]["name"],
                identifiers=[Identifier(identifier["key"], identifier["value"], identifier["is_part_of_uniqueness"]) for
                             identifier in json["adapter_key"]["identifiers"]]))
        if type(json["credential_config"]) is dict:
            self.credentials = json["credential_config"]["credential_fields"]
        else:
            self.credentials = None
        self.suite_api_client = VROpsSuiteApiClient()
        self.certificates = json["certificate_config"]["certificates"]

    @classmethod
    def from_input(cls, infile):
        return cls(read_from_pipe(infile))
