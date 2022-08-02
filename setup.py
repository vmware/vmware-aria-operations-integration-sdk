#!/usr/bin/env python

#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

from setuptools import setup

setup(
    version="0.1.0",
    name="vrops-adapter-tools",
    description="A set of tools to help users build, develop, and distribute containerized Management Packs",
    python_requires=">=3.9",
    install_requires=[
        "docker==5.0.3",
        "Pillow==9.1.0",
        "prompt_toolkit==3.0.29",
        "requests==2.27.1",
        "urllib3==1.26.9",
        "common==0.1.2",
        "templates==0.0.5",
        "flask==2.1.1",
        "openapi_core==0.14.2",
        "GitPython==3.1.27",
        "xmlschema==1.11.3"
    ],
    include_package_data=True,
    package_dir={
        "common": "tools/common",
        "templates": "tools/templates",
        "api": "tools/api",
        "": "tools"
    },
    py_modules=[
        "init",
        "build",
        "mp_test"
    ],
    packages=[
        "common",
        "common.validation",
        "templates",
    ],
    entry_points={
        "console_scripts": [
            "mp-init=init:main",
            "mp-build=build:main",
            "mp-test=mp_test:main"
        ]
    }
)
