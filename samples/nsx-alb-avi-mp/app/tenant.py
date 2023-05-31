#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import logging
from typing import List

import constants
from aria.ops.data import Metric
from aria.ops.object import Identifier
from aria.ops.object import Key
from aria.ops.object import Object
from avi.sdk.avi_api import ApiSession
from cloud import Cloud

logger = logging.getLogger(__name__)


class Tenant(Object):
    """A tenant is an isolated instance of Avi. Each Avi user account is associated with one or more
    tenants. The tenant associated with a user account defines the resources that user can access within
    Avi.

    Extending the Object facilitates adding children, events, metrics, properties, and generation a json representation
    compliant with the Open SDK

    Defining resources helps standardize the unique keys to a resource and it also allows for differentiation
    when adding children, and events.

    Tenant is the only resource type where the name is the same as their UUID; therefore, the name of a tenant must be
    unique

    If a Tenant does not have a uuid and name, is considered to be unidentifiable, or a misconfiguration
    """

    def __init__(self, name: str, uuid: str, url: str):
        """Initializes a Tenant object that represent the ResourceKind defined in line 15 of the describe.xml file.

        :param name: The  unique name of used to display the tenant
        :param uuid: A Universal Unique Identifier for the Tenant
        :param url: A URL with the AVI controller, and the tenant's UUID
        """
        self.uuid = uuid
        self.url = url
        super().__init__(
            key=Key(
                name=name,
                # adapter_kind should match the key defined for the AdapterKind in line 4 of the describe.xml
                adapter_kind=constants.ADAPTER_KIND,
                # object_kind should match the key used for the ResourceKind in line 15 of the describe.xml
                object_kind="tenant",
                identifiers=[Identifier(key="uuid", value=uuid)],
            )
        )


def get_tenants(api: ApiSession) -> List[Tenant]:
    """Fetches all tenant objects from the API; instantiates a Tenant object per JSON tenant object, and returns a list
    of all tenants

    :param api: AVISession object
    :return: A list of all Tenant Objects collected, along with their properties, and metrics
    """
    tenants = []
    results = {}

    # Logging key errors can help diagnose issues with the adapter, and prevent unexpected behavior.
    try:
        results = api.get("tenant?page_size=200").json()["results"]
    except Exception as api_error:
        logger.debug(f"Error during tenant retrieval: {api_error}")

    for tenant in results:
        """Log any Exceptions during collection, instead of returning an error. Individual Resources may fail due to
        missing keys (service misconfiguration) or during api calls to obtain other metrics. In some rare cases, the
        session might expire during the collection.
        """
        try:
            new_tenant = Tenant(
                name=tenant["name"], uuid=tenant["uuid"], url=tenant["url"]
            )
            new_tenant.add_metric(
                Metric(
                    key="clouds",
                    value=api.get(
                        "cloud", headers={"X-Avi-Tenant-UUID": tenant["uuid"]}
                    ).json()["count"],
                )
            )
            tenants.append(new_tenant)
        except Exception as tenant_error:
            logger.debug(
                f'Error during creation of tenant {tenant["name"]} with error message: {tenant_error} '
            )

    # TODO: If no tenants were collected, we should return an error message
    return tenants


def add_tenant_children(tenants: List[Tenant], clouds: List[Cloud]) -> List[Tenant]:
    """Adds all children related to the tenant. Resource relationships should only be made as parent child,
    not Grandparent child.

    :param tenants: A list of Tenant resources
    :param clouds: A list of Cloud resources
    :return: A list of Tenants with their added relations, if any
    """
    for tenant in tenants:
        # A tenant can have many clouds related to itself
        children = filter(lambda c: c.parent_tenant_url == tenant.url, clouds)

        # Add each Cloud to their related Tenant
        for child in children:
            tenant.add_child(child)

    return tenants
