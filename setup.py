#!/usr/bin/env python
import os

from setuptools import setup

import tools.common.filesystem as filesystem

repo_path = os.getenv("VROPS_SDK_REPO_PATH")

if repo_path is None:
    print("VROPS_SDK_REPO_PATH not found")
    print("To install this package run 'install.sh'.")
    print("Alternatively, set the environment variable 'VROPS_SDK_REPO_PATH' to the path of the 'vrops-python-sdk' repository and rerun this command.")
    exit(1)
else:
    filesystem.get_root_directory(default_path=lambda: repo_path)

setup(
    name="vrops-adapter-tools",
    description="A set of tools to help users build, develop, and distribute containerized Management Packs",
    install_requires=[
        "docker",
        "Pillow",
        "PyInquirer",
        "requests",
        "urllib3",
        "common",
        "templates",
        "flask",
        "openapi_core"
    ],
    package_dir={
        "common": "tools/common",
        "templates": "tools/templates",
        "": "tools"
    },
    py_modules=[
        "init",
        "build",
        "mp_test"
    ],
    packages=[
        "common",
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
