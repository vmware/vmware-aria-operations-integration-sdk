#!/usr/bin/env python

#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

from setuptools import setup

setup(
    version="0.2.0",
    name="vrealize_operations_integration_sdk",
    description="A set of tools to help users build, develop, and distribute containerized Management Packs",
    project_urls={
        "Source": "https://github.com/vmware/vrealize-operations-integration-sdk",
        "Tracker": "https://github.com/vmware/vrealize-operations-integration-sdk/issues"
    },
    python_requires=">=3.9",
    install_requires=[
        "docker==6.0.0",
        "Pillow==9.1.0",
        "sen==0.6.2",
        "prompt_toolkit==3.0.29",
        "requests==2.27.1",
        "urllib3==1.26.9",
        "flask==2.1.1",
        "openapi_core==0.14.2",
        "GitPython==3.1.27",
        "xmlschema==1.11.3",
        "httpx==0.23.0",
        "validators==0.20.0"
    ],
    include_package_data=True,
    packages=[
        "vrealize_operations_integration_sdk",
        "vrealize_operations_integration_sdk.adapter_template",
        "vrealize_operations_integration_sdk.api",
        "vrealize_operations_integration_sdk.validation"
    ],
    entry_points={
        "console_scripts": [
            "mp-init=vrealize_operations_integration_sdk.mp_init:main",
            "mp-build=vrealize_operations_integration_sdk.mp_build:main",
            "mp-test=vrealize_operations_integration_sdk.mp_test:main"
        ]
    }
)
