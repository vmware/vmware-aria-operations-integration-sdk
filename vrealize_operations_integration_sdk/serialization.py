#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import datetime
import json
import time

from vrealize_operations_integration_sdk.collection_statistics import CollectionStatistics


class CollectionBundle:
    def __init__(self, request, response, duration, container_stats):
        self.request = request
        self.response = response
        self.duration = duration
        self.container_stats = container_stats
        # self.collection_number = #TODO: get collection_number
        # self.time_stamp = time.time() #TODO: get timestamp
        self.failed = not response or not response.is_success or "errorMessage" in response.text
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
        else:
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
