from vrops.object import Key, Identifier
from vrops.pipe_utils import read_from_pipe
from vrops.suite_api_client import VROpsSuiteApiClient


class AdapterInstance:
    def __init__(self, json):
        self.key = Key(json["adapterKey"]["adapterKind"], json["adapterKey"]["objectKind"], json["adapterKey"]["name"],
                       [Identifier(identifier["key"], identifier["value"], identifier["isPartOfUniqueness"]) for
                        identifier in json["adapterKey"]["identifiers"]])
        self.credentials = json["credentialConfig"]["credentialFields"]
        self.suite_api_client = VROpsSuiteApiClient()
        self.certificates = json["certificateConfig"]["certificates"]

    @classmethod
    def from_input(cls, infile):
        return cls(read_from_pipe(infile))
