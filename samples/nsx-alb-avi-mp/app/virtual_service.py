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


class VirtualService(Object):
    """Virtual services are the core of the Avi load-balancing and proxy functionality. A virtual service
    advertises an IP address and ports to the external world and listens for client traffic.
    """

    def __init__(self, name: str, uuid: str, parent_cloud_url: str, url: str):
        """Initializes a VirtualService object that represent the ResourceKind defined in line 23 of the describe.xml
        file.
        :param name: The name used to display the virtual service (not unique)
        :param uuid: A Universal Unique Identifier for the virtual service
        :param parent_cloud_url: A string representation of the Cloud's URL
        :param url: A string representation of the Virtual Service's URL
        """
        self.uuid = uuid
        self.parent_cloud_url = parent_cloud_url
        self.url = url
        super().__init__(
            key=Key(
                name=name,
                adapter_kind=constants.ADAPTER_KIND,
                object_kind="virtual_service",
                identifiers=[Identifier(key="uuid", value=uuid)],
            )
        )


def get_virtual_services(api: ApiSession) -> List[VirtualService]:
    """Fetches all virtual service objects from the API; instantiates a VirtualService object per JSON virtual_service
    object, and returns a list of all virtual services
    :param api:
    :return: A list of all VirtualServices collected, along with their properties, and metrics.
    """
    virtual_services = []
    results = {}
    try:
        results = api.get("virtualservice?page_size=200").json()["results"]
    except Exception as api_error:
        logger.debug(f"Error during virtual services retrieval: {api_error}")

    for virtual_service in results:
        try:
            new_virtual_service = VirtualService(
                name=virtual_service["name"],
                uuid=virtual_service["uuid"],
                parent_cloud_url=virtual_service["cloud_ref"],
                url=virtual_service["url"],
            )
            new_virtual_service.add_property(
                Property(key="cloud_ref", value=virtual_service["cloud_ref"])
            )
            new_virtual_service.add_property(
                Property(
                    key="se_uuid",
                    value=api.get(f'virtualservice/{virtual_service["uuid"]}/dosstat')
                    .json()
                    .pop()["se_uuid"],
                )
            )

            tcp_stats = (
                api.get(f'virtualservice/{virtual_service["uuid"]}/tcpstat')
                .json()
                .pop()
            )
            rx_stats = tcp_stats["rx_stats"]
            tx_stats = tcp_stats["tx_stats"]

            new_virtual_service.add_metric(
                Metric(
                    key="total_packets_received",
                    value=rx_stats["total_packets_received"],
                )
            )
            new_virtual_service.add_metric(
                Metric(
                    key="bytes_received_in_sequence",
                    value=rx_stats["bytes_received_in_sequence"],
                )
            )
            new_virtual_service.add_metric(
                Metric(key="total_packets_sent", value=tx_stats["total_packets_sent"])
            )
            new_virtual_service.add_metric(
                Metric(key="data_bytes_sent", value=tx_stats["data_bytes_sent"])
            )
            virtual_services.append(new_virtual_service)
        except Exception as virtual_service_error:
            logger.debug(
                f'Error during creation of virtual service {virtual_service["name"]} with error message: {virtual_service_error} '
            )
    return virtual_services


def add_virtual_services_children(
    virtual_services: List[VirtualService], service_engines: List[ServiceEngine]
) -> List[VirtualService]:
    """Adds all children related to the cloud.

    :param virtual_services: A list of VirtualServices
    :param service_engines: a list of ServiceEngines
    :return: A list of VirtualServices with their added relations, if any
    """
    for virtual_service in virtual_services:
        # Matching Service Service Engine Groups to each virtual_service
        for child in filter(
            lambda se: virtual_service.url in se.parent_vs_url, service_engines
        ):
            virtual_service.add_child(child)

    return virtual_services
