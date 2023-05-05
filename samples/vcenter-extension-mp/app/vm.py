#  Copyright 2023 VMware, Inc.
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


def add_vm_metrics(
    suite_api_client: SuiteApiClient,
    adapter_instance_id: str,
    result: CollectResult,
    content: Any,  # vim.ServiceInstanceContent
) -> None:
    container = content.rootFolder  # starting point to look into
    view_type = [vim.VirtualMachine]  # object types to look for
    recursive = True  # whether we should look into it recursively
    container_view = content.viewManager.CreateContainerView(
        container, view_type, recursive
    )

    vms: List[Object] = suite_api_client.query_for_resources(
        {
            "adapterKind": [VCENTER_ADAPTER_KIND],
            "resourceKind": ["VirtualMachine"],
            "adapterInstanceId": [adapter_instance_id],
        }
    )

    vms_by_instance_uuid: dict[str, Object] = {
        vm.get_identifier_value("VMEntityInstanceUUID"): vm for vm in vms
    }

    children = container_view.view
    for virtual_machine in children:
        vm = vms_by_instance_uuid.get(virtual_machine.summary.config.instanceUuid)
        if vm:
            vm.with_property(
                "VirtualDisk|Disk Consolidation Needed",
                str(virtual_machine.summary.runtime.consolidationNeeded),
            )
            result.add_object(vm)
        else:
            logger.warning(
                f"Could not find VM '{virtual_machine.summary.config.name}' with UUID: {virtual_machine.summary.config.instanceUuid}."
            )
