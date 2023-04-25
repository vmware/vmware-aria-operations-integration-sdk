import connexion
import six

from swagger_server.models.adapter_config import AdapterConfig  # noqa: E501
from swagger_server.models.adapter_definition import AdapterDefinition  # noqa: E501
from swagger_server.models.api_version import ApiVersion  # noqa: E501
from swagger_server.models.collect_result import CollectResult  # noqa: E501
from swagger_server.models.endpoint_results import EndpointResults  # noqa: E501
from swagger_server.models.test_result import TestResult  # noqa: E501
from swagger_server import util


def api_version():  # noqa: E501
    """API Version

    Get API Version # noqa: E501


    :rtype: ApiVersion
    """
    return 'do some magic!'


def collect(body=None):  # noqa: E501
    """Data Collection

    Do data collection # noqa: E501

    :param body: 
    :type body: dict | bytes

    :rtype: CollectResult
    """
    if connexion.request.is_json:
        body = AdapterConfig.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def definition():  # noqa: E501
    """Retrieve the data model for collection

    Get Adapter Definition # noqa: E501


    :rtype: AdapterDefinition
    """
    return 'do some magic!'


def get_endpoint_urls(body=None):  # noqa: E501
    """Retrieve endpoint URLs

    This should return a list of properly formed endpoint URL(s) (https://ip address) this adapter instance is expected to communicate with. List of URLs will be used for taking advantage of the VMware Aria Operations Manager certificate trust system. If the list is empty this means adapter will handle certificates manually. # noqa: E501

    :param body: 
    :type body: dict | bytes

    :rtype: EndpointResults
    """
    if connexion.request.is_json:
        body = AdapterConfig.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def test(body=None):  # noqa: E501
    """Connection Test

    Trigger a connection test # noqa: E501

    :param body: 
    :type body: dict | bytes

    :rtype: TestResult
    """
    if connexion.request.is_json:
        body = AdapterConfig.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
