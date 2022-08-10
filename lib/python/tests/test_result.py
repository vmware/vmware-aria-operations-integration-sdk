#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

from vrops.result import TestResult


def test_empty_test_result():
    tr = TestResult()
    assert "errorMessage" not in tr.get_json()


def test_error_test_result():
    error_message = "Test Error Message"
    tr = TestResult()
    tr.with_error(error_message)
    assert "errorMessage" in tr.get_json()
    assert tr.get_json()["errorMessage"] == error_message
