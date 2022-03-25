# coding: utf-8

from setuptools import setup, find_packages
from tools.common.config import get_config_value

NAME = "swagger_server"

# If The version is not present in the config file, we shouldn't ask the user for one.
VERSION = get_config_value(f'{NAME}_version', '-1.0.0')
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["connexion"]

setup(
    name=NAME,
    version=VERSION,
    description="Adapter API",
    author_email="",
    url="",
    keywords=["Swagger", "Adapter API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['swagger/swagger.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['swagger_server=swagger_server.__main__:main']},
    long_description="""\
    The API contract is defined using a standard OpenAPI specification to simplify adapter development.
    """
)
