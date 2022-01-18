import configparser
import subprocess

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

    if body is None:
        return "No body in request", 400

    command = getcommand("collect")
    environment = getenv(body)
    invocation = command + [str(body.adapter_key)]

    return runcommand(invocation, environment)


def test(body=None):  # noqa: E501
    """Connection Test

    Trigger a connection test # noqa: E501

    :param body: 
    :type body: dict | bytes

    :rtype: TestResult
    """
    if connexion.request.is_json:
        body = AdapterConfig.from_dict(connexion.request.get_json())  # noqa: E501

    if body is None:
        return "No body in request", 400

    command = getcommand("test")
    environment = getenv(body)
    invocation = command + [str(body.adapter_key)]

    return runcommand(invocation, environment)


def version():  # noqa: E501
    """Adapter Version

    Get Adapter Version # noqa: E501


    :rtype: str
    """

    config = configparser.ConfigParser()
    config.read("commands.cfg")
    return config["Version"]["major"] + "." + config["Version"]["minor"]


def getcommand(commandtype):
    config = configparser.ConfigParser()
    config.read("commands.cfg")
    print(f"config={config.sections()}")
    command = str(config["Commands"][commandtype])
    print(config["Commands"])
    print(config["Commands"][commandtype])
    return command.split(" ")


def getenv(body):
    env = {
        "ADAPTER_KIND": body.adapter_key.adapter_kind,
        "ADAPTER_INSTANCE_OBJECT_KIND": body.adapter_key.object_kind,
        "SUITE_API_USER": body.internal_rest_credential.user_name,
        "SUITE_API_PASSWORD": body.internal_rest_credential.password
    }
    for credential_field in body.credential.credential_fields:
        env[f"CREDENTIAL_{credential_field.key.upper()}"] = credential_field.value

    return env


def runcommand(command, environment=None):
    print(f"Running command {repr(command)}")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                               env=environment)
    stdout, stderr = process.communicate()

    return stdout
