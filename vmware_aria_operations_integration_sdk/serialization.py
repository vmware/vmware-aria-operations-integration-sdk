#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import json
import logging
import os
import ssl
import time
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from httpx import Response
from requests import Request

from vmware_aria_operations_integration_sdk.collection_statistics import (
    CollectionStatistics,
)
from vmware_aria_operations_integration_sdk.collection_statistics import (
    LongCollectionStatistics,
)
from vmware_aria_operations_integration_sdk.containerized_adapter_rest_api import (
    get_failure_message,
)
from vmware_aria_operations_integration_sdk.docker_wrapper import ContainerStats
from vmware_aria_operations_integration_sdk.logging_format import CustomFormatter
from vmware_aria_operations_integration_sdk.logging_format import PTKHandler
from vmware_aria_operations_integration_sdk.project import Project
from vmware_aria_operations_integration_sdk.util import LazyAttribute
from vmware_aria_operations_integration_sdk.validation.adapter_definition_validator import (
    validate_adapter_definition,
)
from vmware_aria_operations_integration_sdk.validation.api_response_validation import (
    validate_api_response,
)
from vmware_aria_operations_integration_sdk.validation.api_response_validation import (
    validate_definition_api_response,
)
from vmware_aria_operations_integration_sdk.validation.describe_checks import (
    cross_check_collection_with_describe,
)
from vmware_aria_operations_integration_sdk.validation.endpoint_url_validator import (
    validate_endpoint,
)
from vmware_aria_operations_integration_sdk.validation.endpoint_url_validator import (
    validate_endpoint_urls,
)
from vmware_aria_operations_integration_sdk.validation.highlights import (
    highlight_event_growth,
)
from vmware_aria_operations_integration_sdk.validation.highlights import (
    highlight_metric_growth,
)
from vmware_aria_operations_integration_sdk.validation.highlights import (
    highlight_object_growth,
)
from vmware_aria_operations_integration_sdk.validation.highlights import (
    highlight_property_growth,
)
from vmware_aria_operations_integration_sdk.validation.highlights import (
    highlight_property_value_growth,
)
from vmware_aria_operations_integration_sdk.validation.relationship_validator import (
    validate_relationships,
)
from vmware_aria_operations_integration_sdk.validation.result import Result

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = PTKHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)


class ResponseBundle:
    def __init__(
        self,
        request: Request,
        response: Response,
        duration: float,
        container_statistics: Optional[ContainerStats],
        validators: List[Callable],
    ) -> None:
        self.response = response
        self.request = request
        self.duration = duration
        self.container_statistics = container_statistics
        self.validators = validators

    def validate(self, project: Project) -> Result:
        result = Result()
        for _validate in self.validators:
            result += _validate(project, self.request, self.response)

        return result

    def serialize(self) -> None:
        # TODO look into Pickle vs JSON
        pass

    def failed(self) -> bool:
        return not self.response.is_success or "errorMessage" in self.response.text

    def __repr__(self) -> str:
        if not self.failed():
            _str = (
                json.dumps(json.loads(self.response.text), sort_keys=True, indent=4)
                + "\n\n"
            )
        else:
            _str = f"Failed: {self.get_failure_message()}\n\n"

        if (
            self.response.status_code != 500
        ):  # Allows the error message to be highlighted
            if self.container_statistics:
                _str += str(self.container_statistics.get_table()) + "\n"
            _str += f"Request completed in {self.duration:0.2f} seconds.\n"

        return _str

    def get_failure_message(self) -> str:
        return get_failure_message(self.response)


class CollectionBundle(ResponseBundle):
    def __init__(
        self,
        request: Request,
        response: Response,
        duration: float,
        container_statistics: Optional[ContainerStats],
    ) -> None:
        super().__init__(
            request,
            response,
            duration,
            container_statistics,
            validators=[
                validate_api_response,
                cross_check_collection_with_describe,
                validate_relationships,
            ],
        )
        self.collection_number = 1
        self.time_stamp = time.time()

    def get_collection_statistics(self) -> Optional[CollectionStatistics]:
        return (
            None
            if self.failed()
            else CollectionStatistics(json.loads(self.response.text))
        )

    def __repr__(self) -> str:
        _str = ""
        if not self.failed():
            _str += (
                json.dumps(json.loads(self.response.text), sort_keys=True, indent=4)
                + "\n"
            )
            _str += repr(self.get_collection_statistics()) + "\n\n"
        else:
            _str += f"Collection Failed: {self.get_failure_message()}\n\n"

        if (
            self.response.status_code != 500
        ):  # Allows the error message to be highlighted
            if self.container_statistics:
                _str += str(self.container_statistics.get_table()) + "\n"
            _str += f"Collection completed in {self.duration:0.2f} seconds.\n"

        return _str


class LongCollectionBundle:
    def __init__(self, collection_interval: float, long_run_duration: float) -> None:
        self.collection_bundles: List[CollectionBundle] = list()
        self.collection_interval: float = collection_interval
        self.long_run_duration: float = long_run_duration

    def __repr__(self) -> str:
        return str(self.long_collection_statistics)

    @LazyAttribute
    def long_collection_statistics(self) -> LongCollectionStatistics:
        return LongCollectionStatistics(
            self.collection_bundles, self.collection_interval, self.long_run_duration
        )

    def validate(self, *args: Any, **kwargs: Any) -> Result:
        """
        Scenario 1: individual objects of the same type are collected, but their identifier keeps changing which
        causes for there to always be the same number of objects, each collection, but overall there is object  growth
        overtime.

        Scenario 2: Every collection returns more and more objects overtime
        :param long_collection_stats:  Contains all the long collections statistics necessary to generate highliights
        :param highlight_file_path: In case we want to save the highlights in a file
        :param verbosity: We should consider giving severity to the highlights just in case the user only wants to see extremely sever ones or all
        """

        result = Result()
        for _validate in [
            highlight_object_growth,
            highlight_metric_growth,
            highlight_property_growth,
            highlight_property_value_growth,
            highlight_event_growth,
        ]:
            result += _validate(self.long_collection_statistics)

        return result

    def add(self, collection_bundle: CollectionBundle) -> None:
        self.collection_bundles.append(collection_bundle)


class ConnectBundle(ResponseBundle):
    def __init__(
        self,
        request: Request,
        response: Response,
        duration: float,
        container_statistics: Optional[ContainerStats],
    ) -> None:
        super().__init__(
            request, response, duration, container_statistics, [validate_api_response]
        )

    def validate(self, project: Project) -> Result:
        result = super().validate(project)
        if self.failed():
            result.with_error(f"Connect attempt failed: {self.get_failure_message()}")
        return result


class EndpointURLsBundle(ResponseBundle):
    def __init__(
        self,
        request: Request,
        response: Response,
        duration: float,
        container_statistics: Optional[ContainerStats],
    ) -> None:
        super().__init__(
            request,
            response,
            duration,
            container_statistics,
            [validate_api_response, validate_endpoint_urls],
        )

    def retrieve_certificates(self) -> Optional[List[Dict]]:
        if not self.response.is_success:
            return None
        endpoints = json.loads(self.response.text).get("endpointUrls", [])
        certificates: List[Dict] = []
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


def _get_certificate_from_endpoint(endpoint: str) -> Optional[Dict]:
    result = validate_endpoint(endpoint)
    if result.error_count > 0:
        logger.warning(
            f"Could not retrieve certificate for {endpoint}: {' '.join([m[1] for m in result.messages])}"
        )
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
            "isExpiredCertificateAccepted": True,
        }
    except ssl.SSLError as e:
        logger.warning(f"Could not retrieve certificate for {endpoint}: {e}")
        return None


def _extract_host_port_from_endpoint(endpoint: str) -> Tuple[str, int]:
    protocol, url = endpoint.split("://", maxsplit=1)
    port = 443
    if ":" in url:
        url, port_str = url.split(":", maxsplit=1)
        if "/" in port_str:
            port_str, _ = port_str.split("/", maxsplit=1)
        try:
            port = int(port_str)
        except ValueError as e:
            port = 443
    if "/" in url:
        url, _ = url.split("/", maxsplit=1)
    return url, port


class AdapterDefinitionBundle(ResponseBundle):
    def __init__(
        self,
        request: Request,
        response: Response,
        duration: float,
        container_statistics: Optional[ContainerStats],
    ) -> None:
        super().__init__(
            request,
            response,
            duration,
            container_statistics,
            [validate_definition_api_response, validate_adapter_definition],
        )

    def __repr__(self) -> str:
        if not self.failed():
            if self.response.status_code == 204:
                _str = "No adapter definition returned.\n\n"
            else:
                _str = (
                    json.dumps(json.loads(self.response.text), sort_keys=True, indent=4)
                    + "\n\n"
                )
        else:
            _str = f"Failed: {self.get_failure_message()}\n\n"

        if (
            self.response.status_code != 500
        ):  # Allows the error message to be highlighted
            if self.container_statistics:
                _str += str(self.container_statistics.get_table()) + "\n"
            _str += f"Request completed in {self.duration:0.2f} seconds.\n"

        return _str


class VersionBundle(ResponseBundle):
    def __init__(
        self,
        request: Request,
        response: Response,
        duration: float,
        container_statistics: Optional[ContainerStats],
    ) -> None:
        super().__init__(
            request, response, duration, container_statistics, [validate_api_response]
        )


class WaitBundle(ResponseBundle):
    def __init__(
        self, duration: float, container_statistics: Optional[ContainerStats]
    ) -> None:
        self.duration = duration
        self.container_statistics = container_statistics

    def validate(self, project: Project) -> Result:
        return Result()

    def failed(self) -> bool:
        return False

    def __repr__(self) -> str:
        _str = "\n"
        if self.container_statistics:
            _str += str(self.container_statistics.get_table()) + "\n"
        _str += f"\nContainer ran for {self.duration:0.2f} seconds."
        return _str
