#!/usr/bin/env python

#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

from setuptools import setup

setup(
    version="0.2.0",
    name="vrealize_operations_integration_sdk",
    description="A set of tools to help users build, develop, and distribute containerized Management Packs",
    python_requires=">=3.9",
    install_requires=[
        "docker==5.0.3",
        "Pillow==9.1.0",
        "prompt_toolkit==3.0.29",
        "requests==2.27.1",
        "urllib3==1.26.9",
        "flask==2.1.1",
        "openapi_core==0.14.2",
        "GitPython==3.1.27",
        "xmlschema==1.11.3",
        "httpx==0.23.0"
    ],
    include_package_data=True,
    package_dir={
        "vrealize_operations_integration_sdk": "tools"
    },
    packages=[
        "vrealize_operations_integration_sdk"
    ],
    entry_points={
        "console_scripts": [
            "mp-init=vrealize_operations_integration_sdk.init:main",
            "mp-build=vrealize_operations_integration_sdk.build:main",
            "mp-test=vrealize_operations_integration_sdk.mp_test:main"
        ]
    }
)
