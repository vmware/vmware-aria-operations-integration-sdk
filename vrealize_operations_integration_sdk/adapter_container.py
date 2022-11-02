#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import json
import time
import logging

import httpx

from vrealize_operations_integration_sdk.constant import API_VERSION_ENDPOINT
from vrealize_operations_integration_sdk.containerized_adapter_rest_api import send_get_to_adapter
from vrealize_operations_integration_sdk.docker_wrapper import init, get_container_image, run_image, stop_container, \
    ContainerStats
from vrealize_operations_integration_sdk.ui import Spinner


logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
consoleHandler = PTKHandler()
consoleHandler.setFormatter(CustomFormatter())
logger.addHandler(consoleHandler)

class AdapterContainer:
    def __init__(self, path):
        self.docker_client = init()
        self.path = path
        self.memory_limit = None
        self.started = False
        self.image = None
        self._image_task = asyncio.wrap_future(get_container_image(self.docker_client, self.path))
        self.container = None
        self._container_task = None
        self.stats = None

    def start(self, memory_limit):
        self.memory_limit = memory_limit
        self._container_task = asyncio.create_task(self._threaded_start())

    async def _threaded_start(self):
        if self._image_task:
            self.image = await self._image_task
            self._image_task = None
        self.container = run_image(self.docker_client, self.image, self.path, self.memory_limit)

    async def stop(self):
        if self._container_task:
            await self._container_task
        if self.container:
            stop_container(self.container)
        self.docker_client.images.prune(filters={"label": "mp-test"})
        self.started = False
        self.container = None

    async def get_container(self):
        if not self.started:
            await self.wait_for_container_startup()
        return self.container

    async def record_stats(self):
        self.stats = ContainerStats(await self.get_container())
        return self.stats

    async def wait_for_container_startup(self):
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
                        request, response, elapsed_time = await send_get_to_adapter(client, API_VERSION_ENDPOINT)
                    version = json.loads(response.text)
                    self.started = True
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    elapsed_time = time.perf_counter() - start_time
                    if elapsed_time > max_wait_time:
                        logger.error(f"HTTP Server did not start after {max_wait_time} seconds")
                        exit(1)
                    await asyncio.sleep(0.5)


