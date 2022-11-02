#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import json
import logging
import math

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class SuiteApiConnectionParameters(object):
    def __init__(self, host: str, username: str, password: str, auth_source: str = "LOCAL"):
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

    def __enter__(self):
        """Acquire a token upon entering the 'with' context

        :return: self
        """
        self.token = self.get_token()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Release the token upon exiting the 'with' context

        :param exception_type: Unused
        :param exception_value: Unused
        :param traceback: Unused
        :return: None
        """
        self.release_token()

    def get_token(self):
        """Get the authentication token

        Gets the current authentication token. If no current token exists, acquires an authentication token first.

        :return: The authentication token
        """
        if self.token == "":
            token_response = self.post("/api/auth/token/acquire", json={
                "username": self.credential.username,
                "password": self.credential.password,
                "authSource": self.credential.auth_source
            })
            if token_response.ok:
                self.token = token_response.json()["token"]
                logger.debug("Acquired token " + self.token)
            else:
                logger.warning(f"Could not acquire SuiteAPI token: {token_response}")

        return self.token

    def release_token(self):
        """Release the authentication token, if it exists

        :return: None
        """
        if self.token != "":
            self.post("auth/token/release")
            self.token = ""

    def get(self, url, **kwargs):
        """Send a GET request to the SuiteAPI

        :param url: URL to send GET request to
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        return self._request_wrapper(requests.get, url, **kwargs)

    def paged_get(self, url, key: str, **kwargs):
        """Send a GET request to the SuiteAPI that gets a paged response

        :param url: URL to send GET request to
        :param key: Json key that contains the paged data
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        return self._paged_request(requests.get, url, key, **kwargs)

    def post(self, url, **kwargs):
        """Send a POST request to the SuiteAPI

        :param url: URL to send POST request to
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        kwargs["headers"].setdefault("Content-Type", "application/json")
        return self._request_wrapper(requests.post, url, **kwargs)

    def paged_post(self, url, key, **kwargs):
        """Send a POST request to the SuiteAPI that gets a paged response.

        :param key: Json key that contains the paged data
        :param url: URL to send POST request to
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        kwargs["headers"].setdefault("Content-Type", "application/json")
        return self._paged_request(requests.post, url, key, **kwargs)

    def put(self, url, **kwargs):
        """Send a PUT request to the SuiteAPI

        :param url: URL to send PUT request to
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        return self._request_wrapper(requests.put, url, **kwargs)

    def patch(self, url, **kwargs):
        """Send a PATCH request to the SuiteAPI

        :param url: URL to send PATCH request to
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        return self._request_wrapper(requests.patch, url, **kwargs)

    def delete(self, url, **kwargs):
        """Send a DELETE request to the SuiteAPI

        :param url: URL to send DELETE request to
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        return self._request_wrapper(requests.delete, url, **kwargs)

    def _add_paging(self, **kwargs):
        kwargs.setdefault("params", {})
        kwargs["params"].setdefault("page", 0)
        kwargs["params"].setdefault("pageSize", 1000)

        if "page" in kwargs:
            kwargs["params"]["page"] = kwargs["page"]
        if "pageSize" in kwargs:
            kwargs["params"]["pageSize"] = kwargs["pageSize"]

        return kwargs

    def _paged_request(self, request_func, url, key: str, **kwargs):
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
        total_objects = int(page_0_body.get("pageInfo", {"totalCount": 1}).get("totalCount", 1))
        page_size = kwargs["pageSize"]
        remaining_pages = math.ceil(total_objects / page_size) - 1
        objects = page_0_body.get("key", [])
        while remaining_pages > 0:
            kwargs = self._add_paging(page=remaining_pages)
            page_n_body = json.loads(self._request_wrapper(request_func, url, **kwargs))
            objects.extend(page_n_body.get("key", []))
            remaining_pages -= 1
        return {key: objects}

    def _request_wrapper(self, request_func, url, **kwargs):
        kwargs = self._to_vrops_request(url, **kwargs)
        result = request_func(**kwargs)
        if result.ok:
            logger.debug(request_func.__name__ + " " + kwargs["url"] + ": OK (" + str(result.status_code) + ")")
        else:
            logger.warning(request_func.__name__ + " " + kwargs["url"] + ": ERROR (" + str(result.status_code) + ")")
            logger.debug(result.text)
        return result

    def _to_vrops_request(self, url, **kwargs):
        kwargs.setdefault("url", url)
        kwargs.setdefault("headers", {})
        kwargs["headers"]["Authorization"] = "vRealizeOpsToken " + self.token
        kwargs["headers"].setdefault("Accept", "application/json")
        kwargs.setdefault("verify", False)
        if kwargs["url"].startswith("http"):
            pass
        elif kwargs["url"].startswith("internal"):
            kwargs["headers"]["X-vRealizeOps-API-use-unsupported"] = "true"
            kwargs["url"] = self.credential.host + "/" + kwargs["url"]
        elif kwargs["url"].startswith("/internal"):
            kwargs["headers"]["X-vRealizeOps-API-use-unsupported"] = "true"
            kwargs["url"] = self.credential.host + kwargs["url"]
        elif kwargs["url"].startswith("api"):
            kwargs["url"] = self.credential.host + "/" + kwargs["url"]
        elif kwargs["url"].startswith("/api"):
            kwargs["url"] = self.credential.host + kwargs["url"]
        elif kwargs["url"].startswith("/"):
            kwargs["url"] = self.credential.host + "/api" + kwargs["url"]
        else:
            kwargs["url"] = self.credential.host + "/api/" + kwargs["url"]
        return kwargs
