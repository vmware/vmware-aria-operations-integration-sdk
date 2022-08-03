#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import subprocess
import os
import docker

from docker.models.containers import Container


def login(docker_registry):
    print(f"Login into {docker_registry}")
    response = subprocess.run(["docker", "login", f"{docker_registry}"])

    # Since we are using a subprocess, we cannot be very specific about the type of failure we get
    if response.returncode != 0:
        raise LoginError

    return docker_registry


def init():
    """ Tries to establish a connection with the docker daemon via unix socket.

    If the connection fails, the error message is parsed to find a coomon error message that could inidicate that the
    daemon isn't running.
    If the message does not match the common error message, then the error is appended to another
    error message.

    :return:  A Docker Client that communicates with the Docker daemon
    """
    try:
        client = docker.from_env()

        return client
    except docker.errors.DockerException as e:
        if "ConnectionRefusedError" in e.args[0]:
            raise InitError(message="Cannot connect to the Docker daemon at unix:///var/run/docker.sock.",
                            recommendation="Check that the docker daemon is running")
        elif "PermissionError" in e.args[0]:
            raise InitError(message="Cannot run docker commands.",
                            recommendation=f"Make sure the user {os.getlogin()} has permissions to run docker")
        else:
            raise InitError(f"ERROR: {e}")


def push_image(client, image_tag):
    """
    Pushes the given image tag and returns the images digest.

    If there is an error during while pushing the image, then it will generate a
    PushError, that the user can handle

    NOTE: An alternate method of parsing the digest from an image would be to
    parse the attributes of an image and then check if the image has repoDigests
    attribute, then we could parse the repo digest (different from digest) to get the digest.


    :param client: the docker client that communicates to the docker daemon
    :param image_tag: An image tag that identifies the image to be pushed
    :return: A string version of the SHA256 digest
    """
    response = client.images.push(image_tag, stream=True, decode=True)

    image_digest = ""

    for line in response:
        if 'aux' in line:
            try:
                image_digest = line['aux']['Digest']
            except KeyError:
                raise PushError("Image digest was not found in response from server")

        elif 'errorDetail' in line:
            raise PushError(line['errorDetail']['message'])

    return image_digest


def build_image(client, path, tag, nocache=True, labels={}):
    try:
        return client.images.build(path=path, tag=tag, nocache=nocache, rm=True, labels=labels)
    except docker.errors.BuildError as error:
        raise BuildError(message=f"ERROR: Unable to build Docker file at {path}:\n {error}")


def stop_container(container: Container):
    container.kill()
    container.remove()


# This code is transcribed from docker's code
# https://github.com/docker/cli/blob/2bfac7fcdafeafbd2f450abb6d1bb3106e4f3ccb/cli/command/container/stats_helpers.go
# #L168
def calculate_cpu_percent_latest_unix(previous_stats, current_stats):
    previous_cpu = previous_stats["cpu_stats"]["cpu_usage"]['total_usage']
    previous_system = previous_stats["cpu_stats"]['system_cpu_usage']

    current_cpu = current_stats["cpu_stats"]["cpu_usage"]['total_usage']
    current_system = current_stats["cpu_stats"]['system_cpu_usage']

    online_cpus = current_stats["cpu_stats"]['online_cpus']

    cpu_percent = 0.0
    cpu_delta = current_cpu - previous_cpu
    system_delta = current_system - previous_system

    if system_delta > 0.0 and cpu_delta > 0.0:
        cpu_percent = (cpu_delta / system_delta) * online_cpus * 100

    return cpu_percent


class DockerWrapperError(Exception):
    def __init__(self, message="", recommendation=""):
        self.message = message
        self.recommendation = recommendation


class LoginError(DockerWrapperError):
    """Raised when there is an error logging into docker"""


class InitError(DockerWrapperError):
    """Raised when there is an error starting the docker client"""


class PushError(DockerWrapperError):
    """Raised when the registry server sends back an error"""


class BuildError(DockerWrapperError):
    """Raised when and error occurs while building the Docker image"""
