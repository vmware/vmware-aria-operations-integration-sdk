import connexion

from swagger_server.models.adapter_config import AdapterConfig  # noqa: E501
from swagger_server.models.collect_result import CollectResult  # noqa: E501
from swagger_server.models.test_result import TestResult  # noqa: E501


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


def version():  # noqa: E501
    """Adapter Version

    Get Adapter Version # noqa: E501


    :rtype: str
    """
    return 'do some magic!'
