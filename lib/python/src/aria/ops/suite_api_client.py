#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import logging
import math
from types import TracebackType
from typing import Any
from typing import Callable
from typing import Optional
from typing import Type

import requests
import urllib3
from requests import Response

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class SuiteApiConnectionParameters(object):
    def __init__(
        self, host: str, username: str, password: str, auth_source: str = "LOCAL"
    ):
        """Initialize SuiteApi Connection Parameters

        :param host: The host to use for connecting to the SuiteAPI.
        :param username: Username used to authenticate to SuiteAPI
        :param password: Password used to authenticate to SuiteAPI
        :param auth_source: Source of authentication
        """
        if "http" in host:
            self.host = f"{host}/suite-api/"
        else:
            self.host = f"https://{host}/suite-api/"
        self.username = username
        self.password = password
        self.auth_source = auth_source


class SuiteApiClient(object):
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

        :param connection_params: Connection parameters for the Suite API.
        """
        self.credential = connection_params
        self.token = ""

    def __enter__(self) -> SuiteApiClient:
        """Acquire a token upon entering the 'with' context

        :return: self
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

        :param exception_type: Unused
        :param exception_value: Unused
        :param traceback: Unused
        :return: None
        """
        self.release_token()

    def get_token(self) -> str:
        """Get the authentication token

        Gets the current authentication token. If no current token exists, acquires an authentication token first.

        :return: The authentication token
        """
        if self.token == "":
            token_response = self.post(
                "/api/auth/token/acquire",
                json={
                    "username": self.credential.username,
                    "password": self.credential.password,
                    "authSource": self.credential.auth_source,
                },
            )
            if token_response.ok:
                self.token = token_response.json()["token"]
                logger.debug("Acquired token " + self.token)
            else:
                logger.warning(f"Could not acquire SuiteAPI token: {token_response}")

        return self.token

    def release_token(self) -> None:
        """Release the authentication token, if it exists

        :return: None
        """
        if self.token != "":
            self.post("auth/token/release")
            self.token = ""

    def get(self, url: str, **kwargs: Any) -> Response:
        """Send a GET request to the SuiteAPI

        :param url: URL to send GET request to
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        return self._request_wrapper(requests.get, url, **kwargs)

    def paged_get(self, url: str, key: str, **kwargs: Any) -> dict:
        """Send a GET request to the SuiteAPI that gets a paged response

        :param url: URL to send GET request to
        :param key: Json key that contains the paged data
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        return self._paged_request(requests.get, url, key, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Response:
        """Send a POST request to the SuiteAPI

        :param url: URL to send POST request to
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        kwargs.setdefault("headers", {})
        kwargs["headers"].setdefault("Content-Type", "application/json")
        return self._request_wrapper(requests.post, url, **kwargs)

    def paged_post(self, url: str, key: str, **kwargs: Any) -> dict:
        """Send a POST request to the SuiteAPI that gets a paged response.

        :param url: URL to send POST request to
        :param key: Json key that contains the paged data
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        kwargs.setdefault("headers", {})
        kwargs["headers"].setdefault("Content-Type", "application/json")
        return self._paged_request(requests.post, url, key, **kwargs)

    def put(self, url: str, **kwargs: Any) -> Response:
        """Send a PUT request to the SuiteAPI

        :param url: URL to send PUT request to
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        return self._request_wrapper(requests.put, url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> Response:
        """Send a PATCH request to the SuiteAPI

        :param url: URL to send PATCH request to
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        return self._request_wrapper(requests.patch, url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Response:
        """Send a DELETE request to the SuiteAPI

        :param url: URL to send DELETE request to
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
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

    def _paged_request(
        self, request_func: Callable, url: str, key: str, **kwargs: Any
    ) -> dict:
        """Send a request to the SuiteAPI that returns a paged response. Each response must have data returned in an
        array at key 'key'. The array from the responses will be combined into a single array and returned in a map of
        the form:
        {
           "{key}": [aggregated data]
        }

        :param url: URL to send request to
        :param key: Json key that contains the paged data
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        kwargs = self._add_paging(**kwargs)
        page_0 = self._request_wrapper(request_func, url, **kwargs)
        page_0_body = json.loads(page_0.text)
        total_objects = int(
            page_0_body.get("pageInfo", {"totalCount": 1}).get("totalCount", 1)
        )
        page_size = kwargs["params"]["pageSize"]
        remaining_pages = math.ceil(total_objects / page_size) - 1
        objects = page_0_body.get(key, [])
        while remaining_pages > 0:
            kwargs = self._add_paging(page=remaining_pages, **kwargs)
            page_n_body = json.loads(
                self._request_wrapper(request_func, url, **kwargs).text
            )
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
