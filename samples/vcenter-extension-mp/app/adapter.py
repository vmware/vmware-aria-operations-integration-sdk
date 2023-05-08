#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import atexit
import json
import sys
from typing import Any
from typing import List
from typing import Optional

import aria.ops.adapter_logging as logging
import constants
from aria.ops.adapter_instance import AdapterInstance
from aria.ops.definition.adapter_definition import AdapterDefinition
from aria.ops.object import Object
from aria.ops.result import CollectResult
from aria.ops.result import EndpointResult
from aria.ops.result import TestResult
from aria.ops.suite_api_client import key_to_object
from aria.ops.suite_api_client import SuiteApiClient
from aria.ops.timer import Timer
from constants import ADAPTER_KIND
from constants import ADAPTER_NAME
from host import add_host_metrics
from pyVim.connect import Disconnect
from pyVim.connect import SmartConnect
from pyVmomi import vim
from vm import add_vm_metrics

logger = logging.getLogger(__name__)


def get_adapter_definition() -> AdapterDefinition:
    with Timer(logger, "Get Adapter Definition"):
        definition = AdapterDefinition(ADAPTER_KIND, ADAPTER_NAME)

        definition.define_string_parameter(
            constants.HOST_IDENTIFIER,
            "vCenter Server",
            description="FQDN or IP address of the vCenter Server instance.",
        )
        definition.define_int_parameter(
            constants.PORT_IDENTIFIER, "Port", default=443, advanced=True
        )

        credential = definition.define_credential_type("vsphere_user", "Credential")
        credential.define_string_parameter(constants.USER_CREDENTIAL, "User Name")
        credential.define_password_parameter(constants.PASSWORD_CREDENTIAL, "Password")

        logger.debug(f"Returning adapter definition: {definition.to_json()}")
    return definition


def test(adapter_instance: AdapterInstance) -> TestResult:
    with Timer(logger, "Test connection"):
        result = TestResult()
        try:
            logger.debug(f"Returning test result: {result.get_json()}")

            service_instance = _get_service_instance(adapter_instance)
            content = service_instance.RetrieveContent()
            logger.info(f"content: {content}")

        except Exception as e:
            logger.error("Unexpected connection test error")
            logger.exception(e)
            result.with_error("Unexpected connection test error: " + repr(e))
        finally:
            return result


def collect(adapter_instance: AdapterInstance) -> CollectResult:
    with Timer(logger, "Collection"):
        result = CollectResult()
        try:
            logger.debug(f"Returning collection result {result.get_json()}")
            service_instance = _get_service_instance(adapter_instance)
            content = service_instance.RetrieveContent()
            logger.error(f"taskManager: {content.taskManager}")

            with adapter_instance.suite_api_client as client:
                adapter_instance_id = _get_vcenter_adapter_instance_id(
                    client, adapter_instance
                )
                if adapter_instance_id is None:
                    result.with_error(
                        f"No vCenter Adapter Instance found matching vCenter Server '{adapter_instance.get_identifier_value(constants.HOST_IDENTIFIER)}'"
                    )
                    return result
                add_vm_metrics(client, adapter_instance_id, result, content)
                add_host_metrics(client, adapter_instance_id, result, content)

        except Exception as e:
            logger.error("Unexpected collection error")
            logger.exception(e)
            result.with_error("Unexpected collection error: " + repr(e))
        finally:
            return result


def get_endpoints(adapter_instance: AdapterInstance) -> EndpointResult:
    with Timer(logger, "Get Endpoints"):
        result = EndpointResult()
        logger.debug(f"Returning endpoints: {result.get_json()}")
        return result


def _get_service_instance(
    adapter_instance: AdapterInstance,
) -> Any:  # vim.ServiceInstance
    host = adapter_instance.get_identifier_value(constants.HOST_IDENTIFIER)
    port = int(adapter_instance.get_identifier_value(constants.PORT_IDENTIFIER, 443))
    user = adapter_instance.get_credential_value(constants.USER_CREDENTIAL)
    password = adapter_instance.get_credential_value(constants.PASSWORD_CREDENTIAL)

    service_instance = SmartConnect(
        host=host, port=port, user=user, pwd=password, disableSslCertValidation=True
    )

    # doing this means you don't need to remember to disconnect your script/objects
    atexit.register(Disconnect, service_instance)

    return service_instance


# Get the ID of the vCenter Adapter Instance that matches the vCenter Server of this
# Extension. We use this to filter resources from VMware Aria Operations to the specific
# vCenter Server we are collecting against to prevent collisions when two objects from
# different vCenters share the same entity ID.
def _get_vcenter_adapter_instance_id(
    client: SuiteApiClient, adapter_instance: Object
) -> Optional[str]:
    ais: List[Object] = client.query_for_resources(
        {
            "adapterKind": [constants.VCENTER_ADAPTER_KIND],
            "resourceKind": ["VMwareAdapter Instance"],
        }
    )
    vcenter_server = adapter_instance.get_identifier_value(constants.HOST_IDENTIFIER)
    for ai in ais:
        logger.debug(
            f"Considering vCenter Adapter Instance with VCURL: {ai.get_identifier_value('VCURL')}"
        )
        if ai.get_identifier_value("VCURL") == vcenter_server:
            return _get_adapter_instance_id(client, ai)
    return None


def _get_adapter_instance_id(
    client: SuiteApiClient, adapter_instance: Object
) -> Optional[Any]:
    response = client.get(
        f"api/adapters?adapterKindKey={adapter_instance.get_key().adapter_kind}"
    )
    if response.status_code < 300:
        for ai in json.loads(response.content).get("adapterInstancesInfoDto", []):
            adapter_instance_key = key_to_object(ai.get("resourceKey")).get_key()
            if adapter_instance_key == adapter_instance.get_key():
                return ai.get("id")
    return None


# Main entry point of the adapter. You should not need to modify anything below this line.
def main(argv: List[str]) -> None:
    logging.setup_logging("adapter.log")
    # Start a new log file by calling 'rotate'. By default, the last five calls will be
    # retained. If the logs are not manually rotated, the 'setup_logging' call should be
    # invoked with the 'max_size' parameter set to a reasonable value, e.g.,
    # 10_489_760 (10MB).
    logging.rotate()
    logger.info(f"Running adapter code with arguments: {argv}")
    if len(argv) != 3:
        # `inputfile` and `outputfile` are always automatically appended to the
        # argument list by the server
        logger.error("Arguments must be <method> <inputfile> <ouputfile>")
        exit(1)

    method = argv[0]

    if method == "test":
        test(AdapterInstance.from_input()).send_results()
    elif method == "endpoint_urls":
        get_endpoints(AdapterInstance.from_input()).send_results()
    elif method == "collect":
        collect(AdapterInstance.from_input()).send_results()
    elif method == "adapter_definition":
        result = get_adapter_definition()
        if type(result) is AdapterDefinition:
            result.send_results()
        else:
            logger.info(
                "get_adapter_definition method did not return an AdapterDefinition"
            )
            exit(1)
    else:
        logger.error(f"Command {method} not found")
        exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
