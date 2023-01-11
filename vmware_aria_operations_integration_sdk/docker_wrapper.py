#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import json
import os
import subprocess
import time
from types import TracebackType
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Type

import docker
from docker import DockerClient
from docker.models.containers import Container
from docker.models.images import Image
from sen.util import calculate_blkio_bytes
from sen.util import calculate_network_bytes

from vmware_aria_operations_integration_sdk.constant import DEFAULT_MEMORY_LIMIT
from vmware_aria_operations_integration_sdk.constant import DEFAULT_PORT
from vmware_aria_operations_integration_sdk.stats import convert_bytes
from vmware_aria_operations_integration_sdk.stats import LongRunStats
from vmware_aria_operations_integration_sdk.threading import threaded
from vmware_aria_operations_integration_sdk.ui import Table


def login(docker_registry: str) -> str:
    print(f"Login into {docker_registry}")
    response = subprocess.run(["docker", "login", f"{docker_registry}"])

    # Since we are using a subprocess, we cannot be very specific about the type of failure we get
    if response.returncode != 0:
        raise LoginError

    return docker_registry


def init() -> DockerClient:
    """Tries to establish a connection with the docker daemon via unix socket.

    If the connection fails, the error message is parsed to find a common error message that could indicate that the
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
            raise InitError(
                message="Cannot connect to the Docker daemon",
                recommendation="Ensure the docker daemon is running",
            )
        elif "PermissionError" in e.args[0]:
            raise InitError(
                message="Cannot run docker commands.",
                recommendation=f"Make sure the user {os.getlogin()} has permissions to run docker",
            )
        else:
            raise InitError(e)


def push_image(client: DockerClient, image_tag: str) -> str:
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
        if "aux" in line:
            try:
                image_digest = line["aux"]["Digest"]
            except KeyError:
                raise PushError("Image digest was not found in response from server")

        elif "errorDetail" in line:
            raise PushError(line["errorDetail"]["message"])

    return image_digest


def build_image(
    client: DockerClient,
    path: str,
    tag: str,
    nocache: bool = True,
    labels: Optional[Dict[str, str]] = None,
) -> Tuple[Image, Any]:
    """
    Wraps the docker clients images.build method with some appropriate default values
    :param client: Docker client
    :param path: path to the directory containing the dockerfile
    :param tag: Tag for the image
    :param nocache: Do not use the cache when building if this is set. Defaults to true (set)
    :param labels: dict of labels. Defaults to empty dict
    :return:
    """
    if labels is None:
        labels = dict()
    try:
        return client.images.build(  # type: ignore
            path=path, tag=tag, nocache=nocache, rm=True, labels=labels
        )
    except docker.errors.BuildError as error:
        raise BuildError(
            message=f"ERROR: Unable to build Docker file at {path}:\n {error}"
        )


@threaded
def get_container_image(client: DockerClient, build_path: str) -> Image:
    with open(os.path.join(build_path, "manifest.txt")) as manifest_file:
        manifest = json.load(manifest_file)

    docker_image_tag = manifest["name"].lower() + "-test:" + manifest["version"]

    build_image(
        client,
        path=build_path,
        tag=docker_image_tag,
        nocache=False,
        labels={"mp-test": f"{time.time()}"},
    )

    return docker_image_tag


def run_image(
    client: DockerClient,
    image: Image,
    path: str,
    container_memory_limit: Optional[int] = DEFAULT_MEMORY_LIMIT,
) -> Container:
    # Note: errors from running image (e.g., if there is a process using port 8080 it will cause an error) are handled
    # by the try/except block in the 'main' function

    memory_limit = DEFAULT_MEMORY_LIMIT
    if container_memory_limit:
        memory_limit = container_memory_limit

    # Docker memory parameters expect a unit ('m' is 'MB'), or the number will be interpreted as bytes
    # vROps sets the swap memory limit to the memory limit + 512MB, so we will also. The swap memory
    # setting is a combination of memory and swap, so this will limit swap space to a max of 512MB regardless
    # of the memory limit.
    return client.containers.run(
        image,
        detach=True,
        ports={"8080/tcp": DEFAULT_PORT},
        mem_limit=f"{memory_limit}m",
        memswap_limit=f"{memory_limit + 512}m",
        volumes={f"{path}/logs": {"bind": "/var/log/", "mode": "rw"}},
    )


def stop_container(container: Container) -> None:
    container.kill()
    container.remove()


class ContainerStats:
    def __init__(self, container: Container) -> None:
        self.current_memory_usage: List[int] = []
        self.memory_percent_usage: List[float] = []
        self.cpu_percent_usage: List[float] = []
        self.previous_stats: Optional[Dict] = None
        self.container: Container = container
        self._recording: bool = False

    async def __aenter__(self) -> None:
        self.previous_stats = self.container.stats(stream=False)
        self._recording = True
        self._recording_task = asyncio.wrap_future(self._record())

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_value: Optional[BaseException] = None,
        traceback: Optional[TracebackType] = None,
    ) -> None:
        self._recording = False
        await self._recording_task
        self.add(self.container.stats(stream=False))

    @threaded
    def _record(self) -> None:
        last_collection_time = time.perf_counter()
        while self._recording:
            current_time = time.perf_counter()
            if current_time >= last_collection_time + 0.5:
                self.add(self.container.stats(stream=False))
                last_collection_time = current_time
            time.sleep(0.05)

    def add(self, current_stats: Dict) -> None:
        self.block_read, self.block_write = calculate_blkio_bytes(current_stats)
        self.network_read, self.network_write = calculate_network_bytes(current_stats)
        self.total_memory = current_stats["memory_stats"]["limit"]
        current_memory_usage = current_stats["memory_stats"]["usage"]
        self.current_memory_usage.append(current_memory_usage)
        self.memory_percent_usage.append(
            (current_memory_usage / self.total_memory) * 100.0
        )
        cpu = calculate_cpu_percent_latest_unix(self.previous_stats, current_stats)
        if cpu:
            self.cpu_percent_usage.append(cpu)

        self.previous_stats = current_stats

    @classmethod
    def get_summary_headers(cls) -> List[str]:
        """
        Returns an array with the column names for the statistics about the container:
        """
        return [
            "Avg CPU %",
            "Avg Memory Usage %",
            "Memory Limit",
            "Network I/O",
            "Block I/O",
        ]

    def get_summary(self) -> List:
        """
        Returns an array with the statistics about the container:

        :return: ["Avg CPU %", "Avg Memory Usage %", "Memory Limit", "Network I/O", "Block I/O"]
        """
        return [
            LongRunStats(self.cpu_percent_usage, "%"),
            LongRunStats(self.memory_percent_usage, "%"),
            convert_bytes(self.total_memory),
            f"{convert_bytes(self.network_read)} / {convert_bytes(self.network_write)}",
            f"{convert_bytes(self.block_read)} / {convert_bytes(self.block_write)}",
        ]

    def get_table(self) -> Table:
        headers = self.get_summary_headers()
        data = [self.get_summary()]
        return Table(headers, data)


# This code is transcribed from docker's code
# https://github.com/docker/cli/blob/2bfac7fcdafeafbd2f450abb6d1bb3106e4f3ccb/cli/command/container/stats_helpers.go#L168
def calculate_cpu_percent_latest_unix(
    previous_stats: Optional[Dict], current_stats: Dict
) -> Optional[float]:
    if not previous_stats:
        return None

    previous_cpu = previous_stats["cpu_stats"]["cpu_usage"]["total_usage"]
    previous_system = previous_stats["cpu_stats"]["system_cpu_usage"]

    current_cpu = current_stats["cpu_stats"]["cpu_usage"]["total_usage"]
    current_system = current_stats["cpu_stats"]["system_cpu_usage"]

    online_cpus = current_stats["cpu_stats"]["online_cpus"]

    cpu_percent = 0.0
    cpu_delta = current_cpu - previous_cpu
    system_delta = current_system - previous_system

    if system_delta > 0.0 and cpu_delta > 0.0:
        cpu_percent = (cpu_delta / system_delta) * online_cpus * 100

    return cpu_percent


class DockerWrapperError(Exception):
    def __init__(self, message: str = "", recommendation: str = "") -> None:
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
