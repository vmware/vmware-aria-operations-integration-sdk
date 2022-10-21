#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import json
import logging
import os
import ssl
import time
from typing import Tuple, Optional

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

    #TODO: write lazy function
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
        return repr(self.long_collection_statistics)

    @property
    def long_collection_statistics(self) -> LongCollectionStatistics:
        if not hasattr(self, "_calculated_stats"):
            self._calculated_stats = LongCollectionStatistics(self.collection_bundles, self.collection_interval)

        return self._calculated_stats

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
