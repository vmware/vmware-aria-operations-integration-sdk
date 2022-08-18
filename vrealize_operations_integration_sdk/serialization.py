#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import json
import time

from vrealize_operations_integration_sdk.collection_statistics import CollectionStatistics

# NOTE: we could make this a bit more generic maybe move it to the API package and call it ResponseBundle?
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

    def to_html(self):
        pass

    def failed(self):
        return not self.response or not self.response.is_success or "errorMessage" in self.response.text


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
        if not self.failed():
            self.stats = CollectionStatistics(json.loads(response.text), container_stats, duration)
        else:
            self.stats = container_stats

    def __repr__(self):
        return self.stats.__repr__()

# TODO: ConnectBundle
