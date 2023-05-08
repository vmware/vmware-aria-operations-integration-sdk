#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import logging
from typing import Any
from typing import List

from aria.ops.object import Object
from aria.ops.result import CollectResult
from aria.ops.suite_api_client import SuiteApiClient
from constants import VCENTER_ADAPTER_KIND
from pyVmomi import vim

logger = logging.getLogger(__name__)


def add_host_metrics(
    suite_api_client: SuiteApiClient,
    adapter_instance_id: str,
    result: CollectResult,
    content: Any,  # vim.ServiceInstanceContent
) -> None:
    container = content.rootFolder  # starting point to look into
    view_type = [vim.HostSystem]  # object types to look for
    recursive = True  # whether we should look into it recursively
    container_view = content.viewManager.CreateContainerView(
        container, view_type, recursive
    )

    hosts: List[Object] = suite_api_client.query_for_resources(
        {
            "adapterKind": [VCENTER_ADAPTER_KIND],
            "resourceKind": ["HostSystem"],
            "adapterInstanceId": [adapter_instance_id],
        }
    )

    hosts_by_name: dict[str, Object] = {
        f"vim.HostSystem:{host.get_identifier_value('VMEntityObjectID')}": host
        for host in hosts
    }

    children = container_view.view
    for host_system in children:
        h = repr(host_system.config.host).strip("'")  # Remove quotes
        host = hosts_by_name.get(h)
        if host:
            for stack in host_system.config.network.netStackInstance:
                logger.info(f"net|Network Stack:{stack.key}|TCP/IP Stack Type")
                host.with_property(
                    f"net|Network Stack:{stack.key}|TCP/IP Stack Type", stack.key
                )
                host.with_property(
                    f"net|Network Stack:{stack.key}|VMkernel Gateway IP",
                    str(stack.ipRouteConfig.defaultGateway),
                )
                host.with_property(
                    f"net|Network Stack:{stack.key}|Gateway Is Configured",
                    bool(stack.ipRouteConfig.defaultGateway),
                )
            result.add_object(host)
        else:
            logger.warning(
                f"Could not find HostSystem {host_system.config.summary.name} with id '{h}'."
            )
