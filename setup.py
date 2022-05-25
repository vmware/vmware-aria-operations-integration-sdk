#!/usr/bin/env python
import os

from setuptools import setup
from common.repository import get_root_directory



repo_path = os.getenv("VROPS_SDK_REPO_PATH")

if repo_path is None:
    print("VROPS_SDK_REPO_PATH not found")
    print("To install this package run 'install.sh'.")
    print("Alternatively, set the environment variable 'VROPS_SDK_REPO_PATH' to the path of the 'vrops-python-sdk' repository and rerun this command.")
    exit(1)
else:
    get_root_directory(default_path=lambda: repo_path)

setup(
    version="0.0.1",
    name="vrops-adapter-tools",
    description="A set of tools to help users build, develop, and distribute containerized Management Packs",
    python_requires=">=3.3",
    install_requires=[
        "docker==5.0.3",
        "Pillow==9.1.0",
        "prompt_toolkit==3.0.29",
        "requests==2.27.1",
        "urllib3==1.26.9",
        "common==0.1.2",
        "templates==0.0.5",
        "flask==2.1.1",
        "openapi_core==0.14.2"
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
