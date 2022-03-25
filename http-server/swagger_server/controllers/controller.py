import configparser
import json
import logging
import os.path
import subprocess
import tempfile

import connexion

from swagger_server.models.adapter_config import AdapterConfig  # noqa: E501
from swagger_server.models.collect_result import CollectResult  # noqa: E501
from swagger_server.models.test_result import TestResult  # noqa: E501

logger = logging.getLogger(__name__)


def collect(body=None):  # noqa: E501
    """Data Collection

    Do data collection # noqa: E501

    :param body: 
    :type body: dict | bytes

    :rtype: CollectResult
    """
    logger.info("Request: collect")

    if connexion.request.is_json:
        body = AdapterConfig.from_dict(connexion.request.get_json())  # noqa: E501

    if body is None:
        logger.debug("No body in request")
        return "No body in request", 400

    command = getcommand("collect")
    environment = create_env(body)

    return runcommand(command, environment, 202)


def test(body=None):  # noqa: E501
    """Connection Test

    Trigger a connection test # noqa: E501

    :param body: 
    :type body: dict | bytes

    :rtype: TestResult
    """
    logger.info("Request: test")

    if connexion.request.is_json:
        body = AdapterConfig.from_dict(connexion.request.get_json())  # noqa: E501

    if body is None:
        return "No body in request", 400

    command = getcommand("test")
    environment = create_env(body)

    return runcommand(command, environment, 202)


def version():  # noqa: E501
    """Adapter Version

    Get Adapter Version # noqa: E501


    :rtype: str
    """
    logger.info("Request: version")

    config = configparser.ConfigParser()
    config.read("commands.cfg")
    return config["Version"]["major"] + "." + config["Version"]["minor"]


def get_endpoint_urls(body=None):  # noqa: E501
    """Retrieve endpoint URLs

    This should return a list of properly formed endpoint URL(s) (https://ip address) this adapter instance is expected to communicate with. List of URLs will be used for taking advantage of the vRealize Operations Manager certificate trust system. If the list is empty this means adapter will handle certificates manully. # noqa: E501

    :param body:
    :type body: dict | bytes

    :rtype: List[str]
    """
    logger.info("Request: get_endpoint_urls")

    if connexion.request.is_json:
        body = AdapterConfig.from_dict(connexion.request.get_json())  # noqa: E501

    if body is None:
        logger.debug("No body in request")
        return "No body in request", 400

    command = getcommand("endpoint_urls")
    environment = create_env(body)

    return runcommand(command, environment, 200)


def getcommand(commandtype):
    config = configparser.ConfigParser()
    config.read("commands.cfg")
    command = str(config["Commands"][commandtype])
    logger.debug(f"Command: {command}")
    return command.split(" ")


def create_env(body: AdapterConfig):
    logger.debug("Creating environment")
    env = {
        "ADAPTER_KIND": body.adapter_key.adapter_kind,
        "ADAPTER_INSTANCE_OBJECT_KIND": body.adapter_key.object_kind,
        "SUITE_API_USER": body.internal_rest_credential.user_name,
        "SUITE_API_PASSWORD": body.internal_rest_credential.password
    }

    for identifier in body.adapter_key.identifiers:
        env[identifier.key.upper()] = identifier.value

    if body.credential_config:
        for credential_field in body.credential_config.credential_fields:
            env[f"CREDENTIAL_{credential_field.key.upper()}"] = credential_field.value

    return env


def runcommand(command, environment=None, good_response_code=200):
    logger.debug(f"Running command {repr(command)}")
    dir = tempfile.mkdtemp()
    pipe = os.path.join(dir, "output_pipe")
    try:
        os.mkfifo(pipe)
        # TODO: Server should have some timeout mechanism if the adapter hangs or takes too long
        process = subprocess.Popen(command + [pipe], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   universal_newlines=True, env=environment)
    except OSError as e:
        logger.debug(f"Failed to create pipe {pipe}: {e}")
        return "Error initializing adapter communication", 500
    else:
        logger.debug(f"Process created using pipe {pipe}")
        try:
            with open(pipe, "r") as fifo:
                return json.load(fifo), good_response_code
        except Exception as e:
            logger.warning(f"Unknown server error: {e}")
            process.kill()
            return f"Unknown server error", 500
    finally:
        os.unlink(pipe)
        os.rmdir(dir)
