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
        "anyio==3.6.1",
        "attrs==22.1.0",
        "certifi==2022.6.15",
        "charset-normalizer==2.0.12",
        "click==8.1.3",
        "decorator==5.1.1",
        "dictpath==0.1.3",
        "docker==6.0.0",
        "elementpath==2.5.3",
        "Flask==2.1.1",
        "gitdb==4.0.9",
        "GitPython==3.1.27",
        "h11==0.12.0",
        "httpcore==0.15.0",
        "httpx==0.23.0",
        "idna==3.3",
        "importlib-metadata==4.12.0",
        "importlib-resources==5.9.0",
        "isodate==0.6.1",
        "itsdangerous==2.1.2",
        "Jinja2==3.1.2",
        "jsonschema==4.14.0",
        "jsonschema-spec==0.1.2",
        "lazy-object-proxy==1.7.1",
        "MarkupSafe==2.1.1",
        "mock==4.0.3",
        "more-itertools==8.14.0",
        "nest-asyncio==1.5.5",
        "openapi-core==0.15.0",
        "openapi-schema-validator==0.2.3",
        "openapi-spec-validator==0.4.0",
        "packaging==21.3",
        "parse==1.19.0",
        "pathable==0.4.3",
        "Pillow==9.1.0",
        "prompt-toolkit==3.0.29",
        "pyparsing==3.0.9",
        "pyrsistent==0.18.1",
        "PyYAML==6.0",
        "requests==2.27.1",
        "rfc3986==1.5.0",
        "sen==0.6.2",
        "six==1.16.0",
        "smmap==5.0.0",
        "sniffio==1.2.0",
        "typing_extensions==4.3.0",
        "urllib3==1.26.9",
        "urwid==2.1.2",
        "urwidtrees==1.0.3",
        "validators==0.20.0",
        "wcwidth==0.2.5",
        "websocket-client==1.3.3",
        "Werkzeug==2.2.2",
        "xmlschema==1.11.3",
        "zipp==3.8.1",
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
