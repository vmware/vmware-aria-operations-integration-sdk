#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import logging
import os

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class SuiteApiConnectionParameters(object):
    def __init__(self, host: str, username: str, password: str, auth_source: str = "LOCAL"):
        """Initialize SuiteApi Connection Parameters

        :param host: The host to use for connecting to the SuiteAPI. Should include "http://" or "https://"
        :param username: Username used to authenticate to SuiteAPI
        :param password: Password used to authenticate to SuiteAPI
        :param auth_source: Source of authentication
        """
        self.host = host
        self.username = username
        self.password = password
        self.auth_source = auth_source


def get_connection_params():
    """
    :return: Default SuiteApi credentials
    """
    return SuiteApiConnectionParameters(
        # TODO switch to using the provided network instead of the static IP once that is added to the
        #      collector framework api
        #      https://confluence.eng.vmware.com/pages/viewpage.action?spaceKey=Platform&title=CF+2.0%3A+Adapter+to+cluster+communication
        "https://172.17.0.1:443",
        os.getenv("SUITE_API_USER"),
        os.getenv("SUITE_API_PASSWORD")
    )


class VROpsSuiteApiClient(object):
    """Class for simplifying calls to the SuiteAPI

    Automatically handles:
    * Token based authentication
    * Required headers
    * Releasing tokens (when used in a 'with' statement)
    * Logging requests
    * TODO Paging

    This class is intended to be used in a with statement:
    with VROpsSuiteAPIClient() as suiteApiClient:
        # Code using suiteApiClient goes here
        ...
    """

    def __init__(self, connection_params: SuiteApiConnectionParameters = get_connection_params()):
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
        return self._request_wrapper(requests.get, "GET", url, **kwargs)

    def post(self, url, **kwargs):
        """Send a POST request to the SuiteAPI

        :param url: URL to send POST request to
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        return self._request_wrapper(requests.post, "POST", url, **kwargs)

    def put(self, url, **kwargs):
        """Send a PUT request to the SuiteAPI

        :param url: URL to send PUT request to
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        return self._request_wrapper(requests.put, "PUT", url, **kwargs)

    def patch(self, url, **kwargs):
        """Send a PATCH request to the SuiteAPI

        :param url: URL to send PATCH request to
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        return self._request_wrapper(requests.patch, "PATCH", url, **kwargs)

    def delete(self, url, **kwargs):
        """Send a DELETE request to the SuiteAPI

        :param url: URL to send DELETE request to
        :param kwargs: Additional keyword arguments to pass to request
        :return: The API response
        """
        return self._request_wrapper(requests.delete, "DELETE", url, **kwargs)

    def _request_wrapper(self, request_func, request_type, url, **kwargs):
        # TODO: handle paged requests
        kwargs = self._to_vrops_request(url, **kwargs)
        result = request_func(**kwargs)
        if result.ok:
            logger.debug(request_type + " " + kwargs["url"] + ": OK (" + str(result.status_code) + ")")
        else:
            logger.warning(request_type + " " + kwargs["url"] + ": ERROR (" + str(result.status_code) + ")")
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
