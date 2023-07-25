#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import json
import logging
import os
import time
from asyncio import Task
from asyncio.futures import Future
from typing import Optional

import httpx
from docker import DockerClient
from docker.models.containers import Container
from docker.models.images import Image

from vmware_aria_operations_integration_sdk.constant import API_VERSION_ENDPOINT
from vmware_aria_operations_integration_sdk.constant import DEFAULT_PORT
from vmware_aria_operations_integration_sdk.containerized_adapter_rest_api import (
    send_get_to_adapter,
)
from vmware_aria_operations_integration_sdk.docker_wrapper import ContainerStats
from vmware_aria_operations_integration_sdk.docker_wrapper import get_container_image
from vmware_aria_operations_integration_sdk.docker_wrapper import init
from vmware_aria_operations_integration_sdk.docker_wrapper import run_image
from vmware_aria_operations_integration_sdk.docker_wrapper import stop_container
from vmware_aria_operations_integration_sdk.ui import Spinner

logger = logging.getLogger(__name__)


class AdapterContainer:
    def __init__(self, path: str, docker_client: Optional[DockerClient] = None):
        if not docker_client:
            self.docker_client = init()
        else:
            self.docker_client = docker_client
        self.path: str = path
        self.memory_limit: Optional[int] = None
        self.exposed_port: int = DEFAULT_PORT
        self.started: bool = False
        self.image: Optional[Image] = None
        self._image_task: Optional[Future] = asyncio.wrap_future(
            get_container_image(self.docker_client, self.path)
        )
        self.container: Optional[Container] = None
        self._container_task: Optional[Task] = None
        self.stats: Optional[ContainerStats] = None

    def start(self) -> None:
        self.memory_limit = self.memory_limit
        self.exposed_port = self.exposed_port
        self._container_task = asyncio.create_task(self._threaded_start())

    async def _threaded_start(self) -> None:
        if self._image_task:
            self.image = await self._image_task
            self._image_task = None
        self.container = run_image(
            self.docker_client,
            self.image,
            self.path,
            self.memory_limit,
            self.exposed_port,
        )

    async def stop(self) -> None:
        if self._container_task:
            await self._container_task
        if self.container:
            stop_container(self.container)
        self.docker_client.images.prune(filters={"label": "mp-test"})
        self.started = False
        self.container = None

    async def get_container(self) -> Container:
        if not self.started:
            await self.wait_for_container_startup()
        return self.container

    async def record_stats(self) -> ContainerStats:
        self.stats = ContainerStats(await self.get_container())
        return self.stats

    async def wait_for_container_startup(self) -> None:
        if self.started:
            return

        if self._container_task:
            with Spinner("Building adapter"):
                await self._container_task
                self._container_task = None

        # Need time for the server to start
        with Spinner("Waiting for adapter to start"):
            start_time = time.perf_counter()
            max_wait_time = 20
            while not self.started:
                try:
                    async with httpx.AsyncClient(timeout=5) as client:
                        request, response, elapsed_time = await send_get_to_adapter(
                            client, self.exposed_port, API_VERSION_ENDPOINT
                        )
                    version = json.loads(response.text)
                    self.started = True
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    elapsed_time = time.perf_counter() - start_time
                    if elapsed_time > max_wait_time:
                        logger.error(
                            f"HTTP Server did not start after {max_wait_time} seconds"
                        )
                        exit(1)
                    await asyncio.sleep(0.5)
