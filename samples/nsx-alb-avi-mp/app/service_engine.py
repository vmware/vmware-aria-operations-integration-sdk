#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import logging
from typing import List

import constants
from aria.ops.data import Metric
from aria.ops.data import Property
from aria.ops.object import Identifier
from aria.ops.object import Key
from aria.ops.object import Object
from avi.sdk.avi_api import ApiSession

logger = logging.getLogger(__name__)


class ServiceEngine(Object):
    """Avi Service Engines (SEs) handle all data plane operations within Avi by receiving and executing
    instructions from the Controller, a single point of management and control that serves as the “brain”.
    """

    def __init__(
        self, name: str, uuid: str, parent_se_group_url: str, parent_vs_url: List[str]
    ):
        """Initializes a ServiceEngine object that represent the ResourceKind defined in line 29 of the describe.xml
        file
        :param name: The name used to display the service engine (not unique)
        :param uuid: A Universal Unique Identifier for the service engine
        :param parent_se_group_url: A string representation of Service Engine Group, parent to this resource, URL
        :param parent_vs_url: A  list of string representations of the Virtual Service's, parents to this resource, URL
        """
        self.uuid = uuid
        self.parent_se_group_url = parent_se_group_url
        self.parent_vs_url = parent_vs_url
        super().__init__(
            key=Key(
                name=name,
                adapter_kind=constants.ADAPTER_KIND,
                object_kind="service_engine",
                identifiers=[Identifier(key="uuid", value=uuid)],
            )
        )


def get_service_engines(api: ApiSession) -> List[ServiceEngine]:
    """Fetches all service engine objects from the API; instantiates a ServiceEngine object per JSON service_engine
    object, and returns a list of all service engines
    :param api: AVI session object
    :return: A list of all ServiceEngine Objects collected, along with their properties, and metrics
    """
    service_engines = []
    results = {}
    try:
        results = api.get("serviceengine?page_size=200").json()["results"]
    except Exception as api_error:
        logger.debug(f"Error during service engine retrieval: {api_error}")
    for service_engine in results:
        try:
            new_service_engine = ServiceEngine(
                name=service_engine["name"],
                uuid=service_engine["uuid"],
                parent_se_group_url=service_engine["se_group_ref"],
                parent_vs_url=service_engine["vs_refs"],
            )
            new_service_engine.add_property(
                Property(key="controller_ip", value=service_engine["controller_ip"])
            )

            cpu_stats = (
                api.get(f'serviceengine/{service_engine["uuid"]}/cpu/').json().pop()
            )
            new_service_engine.add_metric(
                Metric(
                    key="total_cpu_utilization",
                    value=cpu_stats["total_cpu_utilization"],
                )
            )
            new_service_engine.add_metric(
                Metric(key="total_memory", value=cpu_stats["total_memory"])
            )
            new_service_engine.add_metric(
                Metric(key="free_memory", value=cpu_stats["free_memory"])
            )
            service_engines.append(new_service_engine)
        except Exception as service_engine_error:
            logger.debug(
                f'Error during creation of service engine {service_engine["name"]} with error message: {service_engine_error} '
            )

    return service_engines
