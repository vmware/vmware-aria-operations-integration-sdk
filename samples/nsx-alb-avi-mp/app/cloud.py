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
from service_engine_groups import ServiceEngineGroup
from virtual_service import VirtualService

logger = logging.getLogger(__name__)
""" For a thorough analysis of the structure and logic of the Object representation of a resource, see the tenant.py file.
This file has minor differences from other Resource class definitions.
"""


class Cloud(Object):
    """Clouds are containers for the environment that Avi is installed or operating within."""

    def __init__(
        self,
        name: str,
        uuid: str,
        url: str,
        parent_se_group_template_url: str,
        parent_tenant_url: str,
    ):
        """Initializes a Cloud object that represent the ResourceKind defined in line 19 of the describe.xml file.

        :param name: The name used to display the cloud (not unique)
        :param uuid: A Universal Unique Identifier for the cloud
        :param url: A URL with the AVI controller, and the cloud's UUID
        :param parent_se_group_template_url: A string representation of the Service Engine Group's URL
        :param parent_tenant_url: A string representation of the Tenant's URL
        """
        self.uuid = uuid
        self.url = url
        self.parent_se_group_template_url = parent_se_group_template_url
        self.parent_tenant_url = parent_tenant_url
        super().__init__(
            key=Key(
                name=name,
                adapter_kind=constants.ADAPTER_KIND,
                object_kind="cloud",
                identifiers=[Identifier(key="uuid", value=uuid)],
            )
        )


def get_clouds(api: ApiSession) -> List[Cloud]:
    """Fetches all cloud objects from the API; instantiates a Cloud object per JSON cloud object, and returns a list of
    all clouds

    :param api: AVI session object
    :return: A list of all Cloud Objects collected, along with their properties, and metrics
    """
    clouds = []
    results = {}
    try:
        results = api.get("cloud?page_size=200").json()["results"]
    except Exception as api_error:
        logger.debug(f"Error during cloud retrieval: {api_error}")
    for cloud in results:
        try:
            new_cloud = Cloud(
                name=cloud["name"],
                uuid=cloud["uuid"],
                url=cloud["url"],
                parent_se_group_template_url=cloud["se_group_template_ref"],
                parent_tenant_url=cloud["tenant_ref"],
            )
            new_cloud.add_property(Property(key="license_type", value="license_type"))
            new_cloud.add_metric(
                Metric(
                    key="virtual_services",
                    value=api.get(f'virtualservice?cloud_uuid={cloud["uuid"]}').json()[
                        "count"
                    ],
                )
            )
            clouds.append(new_cloud)
        except Exception as cloud_error:
            logger.debug(
                f'Error during creation of cloud {cloud["name"]} with error message: {cloud_error} '
            )

    return clouds


def add_cloud_children(
    clouds: List[Cloud],
    service_engine_groups: List[ServiceEngineGroup],
    virtual_services: List[VirtualService],
) -> List[Cloud]:
    """Adds all children related to the cloud.

    A resource can be parent to different types of resources

    :param clouds: A list of Cloud resources
    :param service_engine_groups: A list of ServiceEngineGroups
    :param virtual_services: A list of VirtualServices
    :return: A list of Clouds with and their added relations, if any
    """
    for cloud in clouds:
        # Matching Service Service Engine Groups to each Cloud
        for child in filter(
            lambda seg: seg.url == cloud.parent_se_group_template_url,
            service_engine_groups,
        ):
            cloud.add_child(child)

        # Matching Virtual Services to each Cloud
        for child in filter(
            lambda vs: vs.parent_cloud_url == cloud.url, virtual_services
        ):
            cloud.add_child(child)

    return clouds
