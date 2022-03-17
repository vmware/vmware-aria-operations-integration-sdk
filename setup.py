#!/usr/bin/env python

from setuptools import setup

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
        "templates"
    ],
    package_dir={
        "common": "tools/common",
        "templates": "tools/templates",
        "": "tools"
    },
    py_modules=[
        "init",
        "build",
        "test"
    ],
    packages=[
        "common",
        "templates",
    ],
    entry_points={
        "console_scripts": [
            "init=init:main",
            "build=build:main",
            "test=test:main"
        ]
    }
)