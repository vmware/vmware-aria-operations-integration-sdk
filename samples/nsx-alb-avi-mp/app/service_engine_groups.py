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
from service_engine import ServiceEngine

logger = logging.getLogger(__name__)


class ServiceEngineGroup(Object):
    """Service Engines are created within a group, which contains the definition of how the Service Engines should
    be sized, placed, and made highly available.
    Each cloud will have at least one SE group.
    """

    def __init__(self, name: str, uuid: str, url: str):
        """Initializes a ServiceEngineGroup object
        :param name: The name used to display the service engine group (not unique)
        :param uuid: A Universal Unique Identifier for the service engine group
        :param url: A  string representation of URL assigned to this Service Engine Group
        """
        self.uuid = uuid
        self.url = url
        super().__init__(
            key=Key(
                name=name,
                adapter_kind=constants.ADAPTER_KIND,
                object_kind="service_engine_group",
                identifiers=[Identifier(key="uuid", value=uuid)],
            )
        )


def get_service_engine_groups(api: ApiSession) -> List[ServiceEngineGroup]:
    """Fetches all service engine group objects from the API; instantiates a ServiceEngineGroup object per JSON
    service_engine_group object, and returns a list of all service engine groups
    :param api: AVI session object
    :return: A list of all ServiceEngineGroups Objects collected, along with their properties, and metrics
    """
    service_engine_groups = []
    results = {}
    try:
        results = api.get("serviceenginegroup?page_size=200").json()["results"]
    except Exception as api_error:
        logger.debug(f"Error during service engine group retrieval: {api_error}")
    for service_engine_group in results:
        try:
            new_service_engine_group = ServiceEngineGroup(
                name=service_engine_group["name"],
                uuid=service_engine_group["uuid"],
                url=service_engine_group["url"],
            )
            new_service_engine_group.add_property(
                Property(key="license_type", value=service_engine_group["license_type"])
            )
            new_service_engine_group.add_metric(
                Metric(
                    key="service_engines",
                    value=777
                    # TODO calculate number of service engines by counting the number of service enignes that reference
                    #  this SEG by uuid  (se_group_ref": "https://avi-1.tvs.vmware.com/api/serviceenginegroup/uuid)
                )
            )

            service_engine_groups.append(new_service_engine_group)
        except Exception as service_engine_group_error:
            logger.debug(
                f'Error during creation of service engine group {service_engine_group["name"]} with error message: {service_engine_group_error}'
            )

    return service_engine_groups


def add_service_engine_group_children(
    service_engine_groups: List[ServiceEngineGroup],
    service_engines: List[ServiceEngine],
) -> List[ServiceEngineGroup]:
    """Adds all children related to the service engine group.

    :param service_engine_groups: A list of ServiceEngineGroups
    :param service_engines: A list of ServiceEngines
    :return: A list of ServiceEngineGroups with their added relations, if any
    """

    for service_engine_group in service_engine_groups:
        # Matching Service Service Engine Groups to each service_engine_group
        for child in filter(
            lambda se: se.parent_se_group_url == service_engine_group.url,
            service_engines,
        ):
            service_engine_group.add_child(child)

    return service_engine_groups
