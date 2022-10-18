#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from aria.ops import result


def test_empty_test_result():
    # If we import directly as 'TestResult', pytest will try to read it as unit tests (because it begins with 'Test')
    # and emit a warning. Importing as result.TestResult is a workaround to that issue
    tr = result.TestResult()
    assert "errorMessage" not in tr.get_json()


def test_error_test_result():
    error_message = "Test Error Message"
    tr = result.TestResult()
    tr.with_error(error_message)
    assert "errorMessage" in tr.get_json()
    assert tr.get_json()["errorMessage"] == error_message
