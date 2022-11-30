# coding: utf-8
#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from setuptools import find_packages
from setuptools import setup

NAME = "swagger_server"
VERSION = "1.0.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["connexion", "swagger-ui-bundle>=0.0.2"]

setup(
    name=NAME,
    version=VERSION,
    description="Adapter API",
    author_email="",
    url="",
    keywords=["Swagger", "Adapter API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={"": ["swagger/swagger.yaml"]},
    include_package_data=True,
    entry_points={"console_scripts": ["swagger_server=swagger_server.__main__:main"]},
    long_description="""\
    The API contract is defined using a standard OpenAPI specification to simplify adapter development.
    """,
)
