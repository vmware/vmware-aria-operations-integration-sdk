#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0


from vmware_aria_operations_integration_sdk.validation.endpoint_url_validator import validate_endpoint


def test_no_protocol():
    url = "google.com"
    result = validate_endpoint(url)
    assert result.error_count == 1


def test_invalid_protocol():
    url = "http://google.com"
    result = validate_endpoint(url)
    assert result.error_count == 1


def test_valid_url():
    url = "https://google.com"
    result = validate_endpoint(url)
    assert result.error_count == 0


def test_valid_url_with_port():
    url = "https://google.com:443"
    result = validate_endpoint(url)
    assert result.error_count == 0


def test_invalid_url():
    url = "https://google."
    result = validate_endpoint(url)
    assert result.error_count == 1


def test_valid_ip_address():
    url = "https://16.2.5.40"
    result = validate_endpoint(url)
    assert result.error_count == 0


def test_valid_ip_address_with_port():
    url = "https://16.2.5.40:443"
    result = validate_endpoint(url)
    assert result.error_count == 0


def test_invalid_ip_address():
    url = "https://300.2.5.40"
    result = validate_endpoint(url)
    assert result.error_count == 1
