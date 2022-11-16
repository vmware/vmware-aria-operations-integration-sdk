#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import pytest

from vmware_aria_operations_integration_sdk.serialization import _extract_host_port_from_endpoint


def test_host_port_from_valid_endpoint():
    endpoint = "https://rubrik-va.tvs.vmware.com"
    host, port = _extract_host_port_from_endpoint(endpoint)
    assert host == "rubrik-va.tvs.vmware.com"
    assert port == 443  # 443 is the default port


def test_host_port_from_valid_endpoint_with_path():
    endpoint = "https://rubrik-va.tvs.vmware.com/path/"
    host, port = _extract_host_port_from_endpoint(endpoint)
    assert host == "rubrik-va.tvs.vmware.com"
    assert port == 443  # 443 is the default port


def test_host_port_from_valid_endpoint_with_port():
    endpoint = "https://www.google.com:8080"
    host, port = _extract_host_port_from_endpoint(endpoint)
    assert host == "www.google.com"
    assert port == 8080


def test_host_port_from_valid_endpoint_with_port_and_path():
    endpoint = "https://www.google.com:8080/path/subpath/"
    host, port = _extract_host_port_from_endpoint(endpoint)
    assert host == "www.google.com"
    assert port == 8080


def test_host_port_from_invalid_endpoint():
    with pytest.raises(Exception):
        endpoint = "rubrik-va.tvs.vmware.com"  # protocol is required
        host, port = _extract_host_port_from_endpoint(endpoint)