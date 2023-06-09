#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import pytest

from vmware_aria_operations_integration_sdk.mp_build import (
    _is_docker_hub_registry_format,
)


def test_docker_hub_valid_path_includes_docker_io():
    registry_path = "docker.io/namespace/registry_name"
    assert _is_docker_hub_registry_format(registry_path)


def test_docker_hub_valid_path_omits_docker_io():
    registry_path = "namespace/registry_name"
    assert _is_docker_hub_registry_format(registry_path)


def test_docker_hub_invalid_path_ending_char_one():
    registry_path = "namespace/registry_name_"
    assert not _is_docker_hub_registry_format(registry_path)


def test_docker_hub_invalid_path_ending_char_two():
    registry_path = "namespace/registry_name."
    assert not _is_docker_hub_registry_format(registry_path)


def test_docker_hub_invalid_path_ending_char_three():
    registry_path = "namespace/registry_name-"
    assert not _is_docker_hub_registry_format(registry_path)


def test_docker_hub_valid_path_only_letters():
    registry_path = "namespace/registryname"
    assert _is_docker_hub_registry_format(registry_path)


def test_docker_hub_valid_path_spesial_char_one():
    registry_path = "namespace/registry.name"
    assert _is_docker_hub_registry_format(registry_path)


def test_docker_hub_valid_path_spesial_char_two():
    registry_path = "namespace/registry-name"
    assert _is_docker_hub_registry_format(registry_path)


def test_docker_hub_valid_path_spesial_char_three():
    registry_path = "namespace/registry-name.has_many"
    assert _is_docker_hub_registry_format(registry_path)


def test_docker_hub_valid_path_numbers_one():
    registry_path = "namespace/registry-name1"
    assert _is_docker_hub_registry_format(registry_path)


def test_docker_hub_valid_path_numbers_two():
    registry_path = "namespace/1registry-name"
    assert _is_docker_hub_registry_format(registry_path)


def test_docker_hub_valid_path_numbers_three():
    registry_path = "namespace/reg1stry-name"
    assert _is_docker_hub_registry_format(registry_path)


def test_docker_hub_valid_path_namespace_name_one():
    registry_path = "namespace/reg1stry-name"
    assert _is_docker_hub_registry_format(registry_path)


def test_docker_hub_valid_path_namespace_name_two():
    registry_path = "namespace/reg1stry-name"
    assert _is_docker_hub_registry_format(registry_path)


def test_docker_hub_invalid_path_namespace_name_one():
    registry_path = "name_space/reg1stry-name"
    assert not _is_docker_hub_registry_format(registry_path)


def test_docker_hub_invalid_path_namespace_name_two():
    registry_path = "name-space/reg1stry-name"
    assert not _is_docker_hub_registry_format(registry_path)


def test_docker_hub_invalid_path_namespace_name_three():
    registry_path = "name.space/reg1stry-name"
    assert not _is_docker_hub_registry_format(registry_path)
