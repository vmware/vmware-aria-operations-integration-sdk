#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import json
import logging
import os
import ssl
import time
from typing import Tuple, Optional

from util import LazyAttribute
from vrealize_operations_integration_sdk.collection_statistics import CollectionStatistics, LongCollectionStatistics
from vrealize_operations_integration_sdk.logging_format import PTKHandler, CustomFormatter
from vrealize_operations_integration_sdk.validation.api_response_validation import validate_api_response
from vrealize_operations_integration_sdk.validation.describe_checks import cross_check_collection_with_describe
from vrealize_operations_integration_sdk.validation.endpoint_url_validator import validate_endpoint_urls, \
    validate_endpoint
from vrealize_operations_integration_sdk.validation.relationship_validator import validate_relationships
from vrealize_operations_integration_sdk.validation.result import Result

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = PTKHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)


class ResponseBundle:
    def __init__(self, request, response, duration, container_statistics, validators):
        self.response = response
        self.request = request
        self.duration = duration
        self.container_statistics = container_statistics
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
            _str = json.dumps(json.loads(self.response.text), sort_keys=True, indent=4) + "\n\n"
        else:
            _str = f"Failed: {self.get_failure_message()}\n\n"

        if self.response.status_code != 500:  # Allows the error message to be highlighted
            _str += str(self.container_statistics.get_table()) + "\n"
            _str += f"Request completed in {self.duration:0.2f} seconds.\n"

        return _str

    def get_failure_message(self):
        message = ""
        if not self.response.is_success:
            message = f"{self.response.status_code} {self.response.reason_phrase}"
            if hasattr(self.response, "text"):
                encoded = self.response.text.encode('latin1', 'backslashreplace').strip(b'"')
                message += "\n" + encoded.decode('unicode-escape')

        elif "errorMessage" in self.response.text:
            message = json.loads(self.response.text).get('errorMessage')

        return message


class CollectionBundle(ResponseBundle):
    def __init__(self, request, response, duration, container_statistics):
        super().__init__(request, response, duration, container_statistics,
                         validators=[
                             validate_api_response,
                             cross_check_collection_with_describe,
                             validate_relationships])
        self.collection_number = 1
        self.time_stamp = time.time()

    def get_collection_statistics(self):
        return None if self.failed() else CollectionStatistics(json.loads(self.response.text))

    def __repr__(self):
        _str = ""
        if not self.failed():
            _str += json.dumps(json.loads(self.response.text), sort_keys=True, indent=4) + "\n"
            _str += repr(self.get_collection_statistics()) + "\n\n"
        else:
            _str += f"Collection Failed: {self.get_failure_message()}\n\n"

        if self.response.status_code != 500:  # Allows the error message to be highlighted
            _str += str(self.container_statistics.get_table()) + "\n"
            _str += f"Collection completed in {self.duration:0.2f} seconds.\n"

        return _str


class LongCollectionBundle:
    def __init__(self, collection_interval):
        self.collection_bundles = list()
        self.collection_interval = collection_interval

    def __repr__(self):
        return str(self.long_collection_statistics)

    @LazyAttribute
    def long_collection_statistics(self) -> LongCollectionStatistics:
        return LongCollectionStatistics(self.collection_bundles, self.collection_interval)

    def validate(self, *args, **kwargs) -> [str]:
        """
        Scenario 1: individual objects of the same type are collected, but their identifier keeps changing which
        causes for there to always be the same number of objects, each collection, but overall there is object  growth
        overtime.

        Scenario 2: Every collection returns more and more objects overtime
        :param long_collection_stats:  Contains all the long collections statistics necessary to generate highliights
        :param highlight_file_path: In case we want to save the highlights in a file
        :param verbosity: We should consider giving severity to the highlights just in case the user only wants to see extremely sever ones or all
        """
        # Highlight condition / filter objects_types with object growth to asses scenario # 1
        objects_with_growth = [(object_type, stats.objects_growth_rate) for
                               object_type, stats in
                               self.long_collection_statistics.long_object_type_statistics.items()
                               if stats.objects_growth_rate > 0]

        # get overall object growth rate in order to asses scenario # 2
        # find first successful collection and count number of objects
        unique_object_per_collection = [0] * self.long_collection_statistics.total_number_of_collections
        unique_object_per_collection[0] = len(self.collection_bundles[0]
                                              .get_collection_statistics().obj_type_statistics)
        unique_object_per_collection[-1] = len(self.long_collection_statistics.long_object_type_statistics)

        # Calculate growth threshold
        num_collections = self.long_collection_statistics.total_number_of_collections
        # We calculate the growth rate of a new object every 4 collections
        growth_threshold = (((
                (unique_object_per_collection[0] + (num_collections / 4)) / unique_object_per_collection[0])) ** (
                                    1 / num_collections) - 1) * 100

        highlights = Result()

        if len(objects_with_growth):
            for obj_type, growth in objects_with_growth:
                if growth > growth_threshold:
                    new_result = Result()
                    new_result.with_error(f"Object of type {obj_type} displayed growth of {growth:.2f}")
                    highlights += new_result
                else:
                    new_result = Result()
                    new_result.with_warning(f"Object of type {obj_type} displayed negligible growth ({growth:.2f})")
                    highlights += new_result

        return highlights

    def add(self, collection_bundle):
        self.collection_bundles.append(collection_bundle)


class ConnectBundle(ResponseBundle):
    def __init__(self, request, response, duration, container_statistics):
        super().__init__(request, response, duration, container_statistics, [validate_api_response])


class EndpointURLsBundle(ResponseBundle):
    def __init__(self, request, response, duration, container_statistics):
        super().__init__(request, response, duration, container_statistics,
                         [validate_api_response, validate_endpoint_urls])

    def retrieve_certificates(self):
        if not self.response.is_success:
            return None
        endpoints = json.loads(self.response.text).get("endpointUrls", [])
        certificates = []
        if len(endpoints) == 0:
            # If there are no endpoints, we can return an empty list to be saved in a connection
            return certificates
        for endpoint in endpoints:
            cert = _get_certificate_from_endpoint(endpoint)
            if cert:
                certificates.append(cert)
        if certificates:
            # Only return certificates to be saved in a connection if at least one endpoint succeeded.
            return certificates
        return None


def _get_certificate_from_endpoint(endpoint) -> Optional[dict]:
    result = validate_endpoint(endpoint)
    if result.error_count > 0:
        logger.warning(f"Could not retrieve certificate for {endpoint}: {' '.join([m[1] for m in result.messages])}")
        return None
    url, port = _extract_host_port_from_endpoint(endpoint)
    try:
        cert = str(ssl.get_server_certificate((url, port)))
        return {
            "certPemString": cert,
            # VMware Aria Operations defaults 'isInvalidHostnameAccepted' to False, and
            # 'isExpiredCertificateAccepted' to True, so mirror that here
            # These can be changed by manually editing connections in the
            # config.json file. (It's not clear in what circumstances they
            # will change in VMware Aria Operations)
            "isInvalidHostnameAccepted": False,
            "isExpiredCertificateAccepted": True
        }
    except ssl.SSLError as e:
        logger.warning(f"Could not retrieve certificate for {endpoint}: {e}")
        return None


def _extract_host_port_from_endpoint(endpoint) -> Tuple[str, int]:
    protocol, url = endpoint.split("://", maxsplit=1)
    port = 443
    if ":" in url:
        url, port = url.split(":", maxsplit=1)
        if "/" in port:
            port, _ = port.split("/", maxsplit=1)
        try:
            port = int(port)
        except ValueError as e:
            port = 443
    if "/" in url:
        url, _ = url.split("/", maxsplit=1)
    return url, port


class VersionBundle(ResponseBundle):
    def __init__(self, request, response, duration, container_statistics):
        super().__init__(request, response, duration, container_statistics, [validate_api_response])


class WaitBundle:
    def __init__(self, duration, container_statistics):
        self.duration = duration
        self.container_statistics = container_statistics

    def __repr__(self):
        _str = "\n"
        _str += str(self.container_statistics.get_table()) + "\n"
        _str += f"\nContainer ran for {self.duration:0.2f} seconds."
        return _str
