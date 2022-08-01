# coding: utf-8

#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.adapter_config import AdapterConfig  # noqa: E501
from swagger_server.models.collect_result import CollectResult  # noqa: E501
from swagger_server.models.test_result import TestResult  # noqa: E501
from swagger_server.test import BaseTestCase


class TestDefaultController(BaseTestCase):
    """DefaultController integration test stubs"""

    def test_collect(self):
        """Test case for collect

        Data Collection
        """
        body = AdapterConfig()
        response = self.client.open(
            '/collect',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_test(self):
        """Test case for test

        Connection Test
        """
        body = AdapterConfig()
        response = self.client.open(
            '/test',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_version(self):
        """Test case for version

        Adapter Version
        """
        response = self.client.open(
            '/version',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
