#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import json
import time

from vrealize_operations_integration_sdk.collection_statistics import CollectionStatistics

# NOTE: we could make this a bit more generic maybe move it to the API package and call it ResponseBundle?
from vrealize_operations_integration_sdk.validation.result import validate


# Base class and then it stemp onto diferent method classes
class CollectionBundle:
    def __init__(self, request, response, duration, container_stats, project, verbosity, validators=list):
        self.request = request
        self.response = response
        self.duration = duration
        self.container_stats = container_stats
        self.collection_number = 0
        self.time_stamp = time.time()
        self.failed = not response or not response.is_success or "errorMessage" in response.text
        self.validators = validators
        self.project = project
        self.verbosity = verbosity
        self.process_response()

    def serialize(self):
        # TODO look into Pickle vs JSON
        pass

    def to_html(self):
        pass

    def process_response(self):
        # if there is no response then we failed
        # TODO: process result and add message to thi method
        if not self.failed:
            # get/generate json
            # get/generate collection stats
            # get/generate validation results
            self.json = json.loads(self.response.text)
            self.collection_stats = CollectionStatistics(self.json, self.container_stats, self.duration)
            self.results = validate(self.request, self.response, self.duration, self.project,
                                    validators=self.validators, verbosity=self.verbosity)
        else:
            # NOTE: this error message could be part of the validation result
            self.error_message = ""

    def add_validation_results(self):
        pass

    def __repr__(self):
        if self.failed:
            # TODO: return container stats along with the reason behind the error
            return "failed"
        else:
            return self.collection_stats.__repr__()

# TODO: Long Collection Bundle class?
