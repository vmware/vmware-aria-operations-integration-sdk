#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import os
import subprocess

import docker
from docker.models.containers import Container
from sen.util import calculate_blkio_bytes, calculate_network_bytes

from vrealize_operations_integration_sdk.stats import convert_bytes, LongRunStats


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
        if "ConnectionRefusedError" or "FileNotFoundError" or "CreateFile" in e.args[0]:
            raise InitError(message="Cannot connect to the Docker daemon",
                            recommendation="Ensure the docker daemon is running")
        elif "PermissionError" in e.args[0]:
            raise InitError(message="Cannot run docker commands.",
                            recommendation=f"Make sure the user {os.getlogin()} has permissions to run docker")
        else:
            raise InitError(e)


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


class ContainerStats:
    def __init__(self, initial_stats):
        self.current_memory_usage = []
        self.memory_percent_usage = []
        self.cpu_percent_usage = []
        self.previous_stats = initial_stats

    def add(self, current_stats):
        self.block_read, self.block_write = calculate_blkio_bytes(current_stats)
        self.network_read, self.network_write = calculate_network_bytes(current_stats)
        self.total_memory = current_stats["memory_stats"]["limit"]
        current_memory_usage = current_stats["memory_stats"]["usage"]
        self.current_memory_usage.append(current_memory_usage)
        self.memory_percent_usage.append((current_memory_usage / self.total_memory) * 100.0)
        self.cpu_percent_usage.append(calculate_cpu_percent_latest_unix(self.previous_stats, current_stats))

        self.previous_stats = current_stats

    @classmethod
    def get_summary_headers(cls):
        """
        Returns an array with the column names for the statistics about the container:
        """
        return ["Avg CPU %", "Avg Memory Usage %", "Memory Limit", "Network I/O", "Block I/O"]

    def get_summary(self):
        """
        Returns an array with the statistics about the container:

        :return: ["Avg CPU %", "Avg Memory Usage %", "Memory Limit", "Network I/O", "Block I/O"]
        """
        return [
            LongRunStats(self.cpu_percent_usage, "%"),
            LongRunStats(self.memory_percent_usage, "%"),
            convert_bytes(self.total_memory),
            f"{convert_bytes(self.network_read)} / {convert_bytes(self.network_write)}",
            f"{convert_bytes(self.block_read)} / {convert_bytes(self.block_write)}"
        ]


# This code is transcribed from docker's code
# https://github.com/docker/cli/blob/2bfac7fcdafeafbd2f450abb6d1bb3106e4f3ccb/cli/command/container/stats_helpers.go#L168
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
