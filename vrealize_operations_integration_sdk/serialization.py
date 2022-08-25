#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import json
import time

from vrealize_operations_integration_sdk.collection_statistics import CollectionStatistics, LongCollectionStatistics
from vrealize_operations_integration_sdk.ui import Table

from vrealize_operations_integration_sdk.validation.api_response_validation import validate_api_response
from vrealize_operations_integration_sdk.validation.describe_checks import cross_check_collection_with_describe
from vrealize_operations_integration_sdk.validation.relationship_validator import validate_relationships
from vrealize_operations_integration_sdk.validation.result import Result


class ResponseBundle:
    def __init__(self, request, response, duration, validators):
        self.response = response
        self.request = request
        self.duration = duration
        self.validators = validators

    def validate(self, project):
        result = Result()
        for _validate in self.validators:
            result += _validate(project, self.request, self.response)

        return result

    def serialize(self):
        # TODO look into Pickle vs JSON
        pass

    def failed(self):
        return not self.response.is_success or "errorMessage" in self.response.text

    def __repr__(self):
        if not self.failed():
            response = json.dumps(json.loads(self.response.text), sort_keys=True, indent=3)
        else:
            response = f"Failed: {self.get_failure_message()}"

        response += f"\nRequest completed in {self.duration:0.2f} seconds."

        return response

    def get_failure_message(self):
        message = ""
        if not self.response.is_success:
            message = f"{self.response.status_code} {self.response.reason_phrase}"
            if hasattr(self.response, "text"):
                message += "\n" + self.response.text.encode('latin1', 'backslashreplace').decode('unicode-escape')
        elif "errorMessage" in self.response.text:
            message = json.loads(self.response.text).get('errorMessage')

        return message


class CollectionBundle(ResponseBundle):
    def __init__(self, request, response, duration, container_stats):
        super().__init__(request, response, duration,
                         validators=[
                             validate_api_response,
                             cross_check_collection_with_describe,
                             validate_relationships])
        self.container_stats = container_stats
        self.collection_number = 1
        self.time_stamp = time.time()

    def get_collection_statistics(self):
        return None if self.failed() else CollectionStatistics(json.loads(self.response.text))

    def __repr__(self):
        _str = ""
        if not self.failed():
            _str = repr(self.get_collection_statistics()) + "\n"
        else:
            _str = f"Collection Failed: {self.get_failure_message()}\n"

        if self.response.status_code != 500:  # Allows the error message to be highlighted
            headers = ["Avg CPU %", "Avg Memory Usage %", "Memory Limit", "Network I/O", "Block I/O"]
            data = [self.container_stats.get_summary()]
            table = Table(headers, data)
            _str += str(table) + "\n"
            _str += f"Collection completed in {self.duration:0.2f} seconds.\n"

        return _str


class LongCollectionBundle:
    def __init__(self, collection_interval):
        self.collection_bundles = list()
        self.collection_interval = collection_interval

    def __repr__(self):
        return repr(LongCollectionStatistics(self.collection_bundles, self.collection_interval))

    def add(self, collection_bundle):
        self.collection_bundles.append(collection_bundle)


class ConnectBundle(ResponseBundle):
    def __init__(self, request, response, duration):
        super().__init__(request, response, duration, [validate_api_response])


class EndpointURLsBundle(ResponseBundle):
    def __init__(self, request, response, duration):
        super().__init__(request, response, duration, [validate_api_response])


class VersionBundle(ResponseBundle):
    def __init__(self, request, response, duration):
        super().__init__(request, response, duration, [validate_api_response])
