#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import logging
import math
from types import TracebackType
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Type

import requests
import urllib3
from aria.ops.object import Identifier
from aria.ops.object import Key
from aria.ops.object import Object
from requests import Response

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class SuiteApiConnectionParameters:
    def __init__(
        self, host: str, username: str, password: str, auth_source: str = "LOCAL"
    ):
        """Initialize SuiteApi Connection Parameters

        Args:
            host (str): The host to use for connecting to the SuiteAPI.
            username (str): Username used to authenticate to SuiteAPI
            password (str): Password used to authenticate to SuiteAPI
            auth_source (str): Source of authentication. Defaults to "LOCAL"
        """
        if "http" in host:
            self.host = f"{host}/suite-api/"
        else:
            self.host = f"https://{host}/suite-api/"
        self.username = username
        self.password = password
        self.auth_source = auth_source


class SuiteApiClient:
    """Class for simplifying calls to the SuiteAPI

    Automatically handles:
    * Token based authentication
    * Required headers
    * Releasing tokens (when used in a 'with' statement)
    * Paging (when using 'paged_get' or 'paged_post')
    * Logging requests

    This class is intended to be used in a with statement:
    with VROpsSuiteAPIClient() as suiteApiClient:
        # Code using suiteApiClient goes here
        ...
    """

    def __init__(self, connection_params: SuiteApiConnectionParameters):
        """Initializes a SuiteAPI client.

        Args:
             connection_params (SuiteApiConnectionParameters): Connection parameters for the Suite API.
        """
        self.credential = connection_params
        self.token = ""

    def __enter__(self) -> SuiteApiClient:
        """Acquire a token upon entering the 'with' context

        Returns:
            SuiteApiClient: The current instance of the class.
        """
        self.token = self.get_token()
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Release the token upon exiting the 'with' context

        Args:
            exception_type (Optional[Type[BaseException]]): Unused
            exception_value (Optional[BaseException]): Unused
            traceback (Optional[TracebackType]): Unused
        """
        self.release_token()

    def get_token(self) -> str:
        """Get the authentication token

        Gets the current authentication token. If no current token exists, acquires an authentication token first.

        Returns:
             The authentication token
        """
        if self.token == "":
            with self.post(
                "/api/auth/token/acquire",
                json={
                    "username": self.credential.username,
                    "password": self.credential.password,
                    "authSource": self.credential.auth_source,
                },
            ) as token_response:
                if token_response.ok:
                    self.token = token_response.json()["token"]
                    logger.debug("Acquired token " + self.token)
                else:
                    logger.warning(
                        f"Could not acquire SuiteAPI token: {token_response}"
                    )

        return self.token

    def release_token(self) -> None:
        """Release the authentication token, if it exists"""

        if self.token != "":
            self.post("auth/token/release").close()
            self.token = ""

    def get(self, url: str, **kwargs: Any) -> Response:
        """Send a GET request to the SuiteAPI
        The 'Response' object should be used in a 'with' block or
        manually closed after use

        Args:
            url (str): URL to send GET request to
            kwargs (Any): Additional keyword arguments to pass to request

        Returns:
            The API response
        """
        return self._request_wrapper(requests.get, url, **kwargs)

    def paged_get(self, url: str, key: str, **kwargs: Any) -> dict:
        """Send a GET request to the SuiteAPI that gets a paged response

        Args:
            url (str): URL to send GET request to
            key (str): Json key that contains the paged data
            kwargs (Any): Additional keyword arguments to pass to request

        Returns:
             The API response
        """
        return self._paged_request(requests.get, url, key, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Response:
        """Send a POST request to the SuiteAPI
        The 'Response' object should be used in a 'with' block or
        manually closed after use

        Args:
            url (str): URL to send POST request to
            kwargs (Any): Additional keyword arguments to pass to request

        Returns:
             The API response
        """
        kwargs.setdefault("headers", {})
        kwargs["headers"].setdefault("Content-Type", "application/json")
        return self._request_wrapper(requests.post, url, **kwargs)

    def paged_post(self, url: str, key: str, **kwargs: Any) -> dict:
        """Send a POST request to the SuiteAPI that gets a paged response.

        Args:
            url (str): URL to send POST request to
            key (str): Json key that contains the paged data
            kwargs (Any): Additional keyword arguments to pass to request

        Returns:
             The API response
        """
        kwargs.setdefault("headers", {})
        kwargs["headers"].setdefault("Content-Type", "application/json")
        return self._paged_request(requests.post, url, key, **kwargs)

    def put(self, url: str, **kwargs: Any) -> Response:
        """Send a PUT request to the SuiteAPI
        The 'Response' object should be used in a 'with' block or
        manually closed after use

        Args:
            url (str): URL to send PUT request to
            kwargs (Any): Additional keyword arguments to pass to request

        Returns:
             The API response
        """
        return self._request_wrapper(requests.put, url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> Response:
        """Send a PATCH request to the SuiteAPI
        The 'Response' object should be used in a 'with' block or
        manually closed after use

        Args:
            url (str): URL to send PATCH request to
            kwargs (Any): Additional keyword arguments to pass to request

        Returns:
            The API response
        """
        return self._request_wrapper(requests.patch, url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Response:
        """Send a DELETE request to the SuiteAPI
        The 'Response' object should be used in a 'with' block or
        manually closed after use

        Args:
            url (str): URL to send DELETE request to
            kwargs (Any): Additional keyword arguments to pass to request

        Returns:
             The API response
        """
        return self._request_wrapper(requests.delete, url, **kwargs)

    def _add_paging(self, **kwargs: Any) -> dict:
        kwargs.setdefault("params", {})
        kwargs["params"].setdefault("page", 0)
        kwargs["params"].setdefault("pageSize", 1000)

        if "page" in kwargs:
            kwargs["params"]["page"] = kwargs.pop("page")
        if "pageSize" in kwargs:
            kwargs["params"]["pageSize"] = kwargs.pop("pageSize")

        return kwargs

    # Implementations for common endpoints:

    def query_for_resources(self, query: Dict[str, Any]) -> list[Object]:
        """Query for resources using the Suite API, and convert the
        responses to SDK Objects.

        Note that not all information from the query is returned. For example, the
        query returns health statuses of each object, but those are not present in
        the resulting Objects. If information other than the Object itself is needed,
        you will need to call the endpoint and process the results manually.

        Args:
            query (Dict[str, Any]): json of the resourceQuery, as defined in the SuiteAPI docs:
                https://[[aria-ops-hostname]]/suite-api/doc/swagger-ui.html#/Resources/getMatchingResourcesUsingPOST

        Returns:
             list of sdk Objects representing each of the returned objects.
        """
        try:
            results = []
            if "name" in query and "regex" in query:
                # This is behavior in the suite api itself, we're just warning about it
                # here to avoid confusion.
                logger.warning(
                    "'name' and 'regex' are mutually exclusive in resource "
                    "queries. Ignoring the 'regex' key in favor of 'name' "
                    "key."
                )
            # The 'name' key takes an array but only looks up the first element.
            # Fix that limitation here.
            if "name" in query and len(query["name"]) > 1:
                json_body = query.copy()
                # TODO: Improve concurrancy when we add async support
                #  to suite_api_client
                for name in query["name"]:
                    json_body.update({"name": [name]})
                    response = self.paged_post(
                        "/api/resources/query", "resourceList", json=json_body
                    )
                    results.extend(response.get("resourceList", []))
            else:
                response = self.paged_post(
                    "/api/resources/query",
                    "resourceList",
                    json=query,
                )
                results = response.get("resourceList", [])
            return [key_to_object(obj["resourceKey"]) for obj in results]
        except Exception as e:
            logger.error(e)
            logger.exception(e)
            return []

    def _paged_request(
        self, request_func: Callable, url: str, key: str, **kwargs: Any
    ) -> dict:
        """Send a request to the SuiteAPI that returns a paged response. Each response must have data returned in an
        array at key 'key'. The array from the responses will be combined into a single array and returned in a map of
        the form:
        {
           "{key}": [aggregated data]
        }

        Args:
            url(str): URL to send request to
            key (str): Json key that contains the paged data
            kwargs (Any): Additional keyword arguments to pass to request

        Returns:
             The API response
        """
        kwargs = self._add_paging(**kwargs)
        with self._request_wrapper(request_func, url, **kwargs) as page_0:
            if page_0.status_code < 300:
                page_0_body = json.loads(page_0.text)
            else:
                # _request_wrapper will log the error
                # TODO: How should we communicate to caller that
                #       request(s) have failed?
                return {key: []}
        total_objects = int(
            page_0_body.get("pageInfo", {"totalCount": 1}).get("totalCount", 1)
        )
        page_size = kwargs["params"]["pageSize"]
        remaining_pages = math.ceil(total_objects / page_size) - 1
        objects = page_0_body.get(key, [])
        while remaining_pages > 0:
            kwargs = self._add_paging(page=remaining_pages, **kwargs)
            with self._request_wrapper(request_func, url, **kwargs) as page_n:
                if page_n.status_code < 300:
                    page_n_body = json.loads(page_n.text)
            objects.extend(page_n_body.get(key, []))
            remaining_pages -= 1
        return {key: objects}

    def _request_wrapper(
        self, request_func: Callable[..., Response], url: str, **kwargs: Any
    ) -> Response:
        kwargs = self._to_vrops_request(url, **kwargs)
        result = request_func(**kwargs)
        if result.ok:
            logger.info(
                f"{request_func.__name__} {kwargs['url']}: OK({result.status_code})"
            )
        else:
            logger.warning(
                f"{request_func.__name__} {kwargs['url']}: ERROR({result.status_code})"
            )
        logger.debug(result.text)
        return result

    def _to_vrops_request(self, url: str, **kwargs: Any) -> dict:
        kwargs.setdefault("url", url)
        kwargs.setdefault("headers", {})
        if self.token:
            kwargs["headers"]["Authorization"] = "vRealizeOpsToken " + self.token
        kwargs["headers"].setdefault("Accept", "application/json")
        kwargs.setdefault("verify", False)

        url = kwargs["url"]
        if "internal/" in url:
            kwargs["headers"]["X-vRealizeOps-API-use-unsupported"] = "true"
            logger.info(f"Using unsupported API: {url}")
        if url.startswith("http"):
            return kwargs

        if url.startswith("/"):
            url = url[1:]
        if url.startswith("suite-api/"):
            url = url[10:]
        elif url.startswith("api") or url.startswith("internal"):
            kwargs["url"] = self.credential.host + url
        else:
            kwargs["url"] = self.credential.host + "api/" + url
        return kwargs


# Helper methods:


def key_to_object(json_object_key: Dict[str, Any]) -> Object:
    return Object(
        Key(
            json_object_key["adapterKindKey"],
            json_object_key["resourceKindKey"],
            json_object_key["name"],
            [
                Identifier(
                    identifier["identifierType"]["name"],
                    identifier["value"],
                    identifier["identifierType"]["isPartOfUniqueness"],
                )
                for identifier in json_object_key["resourceIdentifiers"]
            ],
        )
    )
