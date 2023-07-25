#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import io
import json
import logging
import os
import platform
import stat
import subprocess
import sys
import tarfile
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
from vmware_aria_operations_integration_sdk.filesystem import files_in_directory
from vmware_aria_operations_integration_sdk.logging_format import CustomFormatter
from vmware_aria_operations_integration_sdk.logging_format import PTKHandler
from vmware_aria_operations_integration_sdk.stats import convert_bytes
from vmware_aria_operations_integration_sdk.stats import LongRunStats
from vmware_aria_operations_integration_sdk.threading import threaded
from vmware_aria_operations_integration_sdk.ui import Table

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = PTKHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)


def login(**kwargs: Any) -> str:
    command = ["docker", "login"]
    if "container_registry" not in kwargs:
        print(f"Login into Docker Hub")
        container_registry = "docker.io"
    else:
        container_registry = kwargs["container_registry"]
        print(f"Login into {container_registry}")
        command.append(container_registry)

    if (
        "registry_username" in kwargs and kwargs["registry_username"] is not None
    ):  # TODO: should be constants
        command.append("--username")
        command.append(kwargs["registry_username"])

    if "registry_password" in kwargs and kwargs["registry_password"] is not None:
        command.append("--password")
        command.append(kwargs["registry_password"])

    response = subprocess.run(command)

    # Since we are using a subprocess, we cannot be very specific about the type of failure we get
    if response.returncode != 0:
        raise LoginError

    return container_registry


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
        # FileNotFoundError(Mac OS and Linux): When the port is not accessible because the advanced setting isn't enabled or the service is not running.
        # ConnectionRefusedError (Linux): When the docker service isn't running on the machine
        # CreateFile (Windows): When docker isn't running in the machine
        if any(
            m in e.args[0]
            for m in ("FileNotFoundError", "ConnectionRefusedError", "CreateFile")
        ):
            logger.debug(e, exc_info=True)

            if platform.system() == "Windows":
                host_os_port_path = "C:\ProgramData\docker"
            else:
                host_os_port_path = "/var/run/docker.dock"

            raise InitError(
                message="Cannot connect to the Docker daemon",
                recommendation=f"Ensure the docker daemon is running and the default socket at {host_os_port_path} is accessible",
            )
        elif "PermissionError" in e.args[0]:
            logger.debug(e, exc_info=True)
            raise InitError(
                message="Cannot run docker commands.",
                recommendation=f"Make sure the user '{os.getlogin()}' has permissions to run docker",
            )
        else:
            raise InitError(e)


def push_image(client: DockerClient, repository: str, tag: str) -> str:
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
    response = client.images.push(
        repository=repository, tag=tag, stream=True, decode=True
    )

    image_digest = ""

    for line in response:
        if "aux" in line:
            try:
                image_digest = line["aux"]["Digest"]
            except KeyError:
                raise PushError("Image digest was not found in response from server")

        elif "errorDetail" in line:
            message = line["errorDetail"]["message"]
            # Clean the error message
            if "unknown: bad request: invalid repository name" in message:
                message = f"Invalid repository name: {message.split(':')[-1]}"
            raise PushError(message)

    return image_digest


def build_image(
    client: DockerClient,
    path: str,
    nocache: bool = True,
    labels: Optional[Dict[str, str]] = None,
    **kwargs: Any,
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
    context = _get_docker_context(path)
    if labels is None:
        labels = dict()
    try:
        return client.images.build(  # type: ignore
            fileobj=context,
            nocache=nocache,
            rm=True,
            labels=labels,
            custom_context=True,
            encoding="gzip",
            **kwargs,
        )
    except docker.errors.BuildError as error:
        raise BuildError(
            message=f"ERROR: Unable to build Docker file at {path}:\n {error}"
        )


def _get_docker_context(directory: str) -> io.BytesIO:
    # In-memory file-like-object for creating the context
    docker_context = io.BytesIO()
    working_directory = os.getcwd()
    try:
        os.chdir(directory)
        with tarfile.open(fileobj=docker_context, mode="w:gz") as context:
            for file in files_in_directory(".", _docker_context_inclusion_func):
                logger.debug(f"Adding '{file}' to image build context")
                context.add(file, recursive=False)
    finally:
        os.chdir(working_directory)
    # In order to read, we have to reset the cursor to the start of the stream
    docker_context.seek(0)
    return docker_context


def _docker_context_inclusion_func(file: str) -> bool:
    excludes = ["build", "content", "logs", "resources"]
    if os.path.dirname(file) == "." and os.path.basename(file) in excludes:
        logger.debug(f"Skipping directory '{file}': Excluded by SDK")
        return False
    elif _is_hidden(file):
        logger.debug(f"Skipping directory '{file}': Hidden")
        return False
    elif _dir_is_venv(file):
        logger.debug(f"Skipping directory '{file}': Virtual Environment")
        return False
    return True


def _is_hidden(file: str) -> bool:
    name = os.path.basename(file)
    # *nix hidden file/dir convention
    if name.startswith("."):
        return True
    # Determine if the file/dir is hidden in Windows
    if sys.platform == "win32":
        if os.stat(file).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN:
            return True
    # Otherwise it isn't hidden
    return False


def _dir_is_venv(directory: str) -> bool:
    if not os.path.isdir(directory):
        return False
    # To determine if a directory is a virtual environment, we look for
    # the 'activate' and 'python' executables. These are in different
    # locations depending on the OS.
    return (  # *nix executable locations
        os.path.exists(os.path.join(directory, "bin", "activate"))
        and os.path.exists(os.path.join(directory, "bin", "python"))
    ) or (  # Windows executable locations
        os.path.exists(os.path.join(directory, "Scripts", "activate.bat"))
        and os.path.exists(os.path.join(directory, "Scripts", "python.exe"))
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
    exposed_port: Optional[int] = DEFAULT_PORT,
) -> Container:
    # Note: errors from running image (e.g., if there is a process using port 8080 it will cause an error) are handled
    # by the try/except block in the 'main' function

    memory_limit = DEFAULT_MEMORY_LIMIT
    if container_memory_limit:
        memory_limit = container_memory_limit

    port = DEFAULT_PORT
    if exposed_port:
        port = exposed_port

    # Docker memory parameters expect a unit ('m' is 'MB'), or the number will be interpreted as bytes
    # vROps sets the swap memory limit to the memory limit + 512MB, so we will also. The swap memory
    # setting is a combination of memory and swap, so this will limit swap space to a max of 512MB regardless
    # of the memory limit.
    return client.containers.run(
        image,
        detach=True,
        ports={"8080/tcp": port},
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
