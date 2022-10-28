#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import configparser
import json
import logging
import os.path
import subprocess
import tempfile
import threading_temp

import connexion

from swagger_server.models import ApiVersion
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

    return runcommand(command, body, 200)


def definition():
    """Get Adapter Definition

    Trigger an adapter definition request # noqa: E501

    :rtype: AdapterDefinition
    """
    logger.info("Request: definition")

    command = getcommand("adapter_definition")
    message, code = runcommand(command)
    if message == "No result from adapter":
        # Special case for this endpoint, since a definition endpoint is not required
        # If we get a 204 error, that is a signal to use a manually-generated describe.xml file
        # if it exists, or generate a temporary stub xml file if it does not.
        return json.loads("{}"), 204
    return message, code


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

    return runcommand(command, body, 200)


def api_version():  # noqa: E501
    """Adapter Version

    Get Adapter Version # noqa: E501


    :rtype: str
    """
    logger.info("Request: apiVersion")
    # This should match the version in swagger_server/swagger/swagger.yaml#/info/version
    return ApiVersion(
        major=1,
        minor=0,
        maintenance=0
    )


def get_endpoint_urls(body=None):  # noqa: E501
    """Retrieve endpoint URLs

    This should return a list of properly formed endpoint URL(s) (https://ip address) this adapter instance is expected to communicate with. List of URLs will be used for taking advantage of the vRealize Operations Manager certificate trust system. If the list is empty this means adapter will handle certificates manully. # noqa: E501

    :param body:
    :type body: dict | bytes

    :rtype: List[str]
    """
    logger.info("Request: endpointURLs")

    if connexion.request.is_json:
        body = AdapterConfig.from_dict(connexion.request.get_json())  # noqa: E501

    if body is None:
        logger.debug("No body in request")
        return "No body in request", 400

    command = getcommand("endpoint_urls")

    return runcommand(command, body, 200)


def getcommand(commandtype):
    config = configparser.ConfigParser()
    config.read("commands.cfg")
    command = str(config["Commands"][commandtype])
    logger.debug(f"Command: {command}")
    return command.split(" ")


def runcommand(command, body: AdapterConfig = None, good_response_code=200):
    logger.debug(f"Running command {repr(command)}")
    dir = tempfile.mkdtemp()
    # These are named from the perspective of the subprocess. We write the subprocess input to the input pipe
    # and read the subprocess output from the output pipe.
    input_pipe = os.path.join(dir, "input_pipe")
    output_pipe = os.path.join(dir, "output_pipe")

    # 'result' holds the adapter result and/or response code that the server should return
    result = [None]

    # Pipe operations are blocking; to prevent deadlocks if the adapter fails to read or write either or both of the
    # pipes, the read/write operations are run in separate threads
    writer_thread = threading.Thread(target=write_adapter_instance, args=(body, input_pipe))
    reader_thread = threading.Thread(target=read_results, args=(output_pipe, result, good_response_code))

    try:
        os.mkfifo(input_pipe)
        os.mkfifo(output_pipe)
        logger.debug("Finished making pipes")
        process = subprocess.Popen(command + [input_pipe, output_pipe], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   universal_newlines=True)
        logger.debug(f"Started process {process.args}")
    except OSError as e:
        logger.debug(f"Failed to create pipe {input_pipe} or {output_pipe}: {e}")
        return "Error initializing adapter communication", 500
    else:
        # Subprocess has successfully started, so start writer and reader threads.
        writer_thread.start()
        reader_thread.start()

        # Wait until the subprocess has exited, and log stdout and stderr (if any)
        out, err = process.communicate()
        logger.debug(out)
        if len(err.strip()) > 0:
            logger.warning(err)

        # process.communicate() will wait until the subprocess has exited. If the subprocess has exited and
        # writer_thread is still alive, then the input was not read. In that case we want the writer_thread to
        # complete, and the easiest way to do that is to read the pipe. It's not required for the adapter info
        # to be read, so this is not (necessarily) an error.
        if writer_thread.is_alive():
            logger.info("Subprocess exited before reading input.")
            with open(input_pipe, "r") as fifo:
                fifo.read()
            writer_thread.join()

        # If the subprocess has exited and reader_thread is still alive, then the adapter didn't write any results.
        # In this case we want the reader_thread to complete but return an error to the user.
        if reader_thread.is_alive():
            logger.error("Subprocess exited before writing result")
            with open(output_pipe, "w") as fifo:
                fifo.write("")
            reader_thread.join()

            message = "No result from adapter"
            if len(err):
                err = err.strip("\n")
                message += f". Captured stderr:\n  {err}"

            return message, 500

        return result[0]
    finally:
        os.unlink(input_pipe)
        os.unlink(output_pipe)
        os.rmdir(dir)


def write_adapter_instance(body, input_pipe):
    try:
        body_dict = body.to_dict() if body else {}

        with open(input_pipe, "w") as fifo:
            logger.debug("Opened input pipe for writing")
            json.dump(body_dict, fifo)

        if body:
            logger.debug(f"Wrote adapter instance to input pipe {input_pipe}:")
            # Don't log sensitive information!
            body_dict["credential_config"] = "REDACTED"
            body_dict["cluster_connection_info"] = "REDACTED"
            logger.debug(f"{json.dumps(body_dict, indent=3)}")

    except Exception as e:
        logger.warning(f"Unknown server error when writing adapter instance to input pipe {input_pipe}: {e}")


def read_results(output_pipe, result, good_response_code):
    try:
        with open(output_pipe, "r") as fifo:
            logger.debug(f"Opened output pipe {fifo} for reading")
            result[0] = json.load(fifo), good_response_code
    except Exception as e:
        logger.warning(f"Unknown server error when reading results: {e}")
        result[0] = "Unknown server error", 500
