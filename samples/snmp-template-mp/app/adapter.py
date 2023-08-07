#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import sys
from typing import List

import aria.ops.adapter_logging as logging
from aria.ops.adapter_instance import AdapterInstance
from aria.ops.definition.adapter_definition import AdapterDefinition
from aria.ops.definition.units import Units
from aria.ops.result import CollectResult
from aria.ops.result import EndpointResult
from aria.ops.result import TestResult
from aria.ops.timer import Timer
from constants import ADAPTER_KIND
from constants import ADAPTER_NAME
from constants import ADDRESS_KEY
from constants import ADMIN_STATUS_KEY
from constants import ADMIN_STATUS_VALUES
from constants import AUTH_PASS_PHRASE
from constants import AUTH_PROTOCOL
from constants import AUTH_PROTOCOLS
from constants import COMMUNITY_STRING
from constants import CONTACT_KEY
from constants import DATA_GROUP
from constants import DATA_KEY
from constants import DESCRIPTION_KEY
from constants import DEVICE_OBJECT
from constants import DISCARDS_KEY
from constants import ERRORS_KEY
from constants import HOSTNAME
from constants import IN_DATA_KEY
from constants import IN_DISCARDS_KEY
from constants import IN_ERRORS_KEY
from constants import IN_UNICAST_KEY
from constants import INTERFACE_ADMIN_STATUS
from constants import INTERFACE_DESCRIPTION
from constants import INTERFACE_IN_DATA
from constants import INTERFACE_IN_DISCARDS
from constants import INTERFACE_IN_ERRORS
from constants import INTERFACE_IN_UNICAST
from constants import INTERFACE_MTU
from constants import INTERFACE_OBJECT
from constants import INTERFACE_OPERATIONAL_STATUS
from constants import INTERFACE_OUT_DATA
from constants import INTERFACE_OUT_DISCARDS
from constants import INTERFACE_OUT_ERRORS
from constants import INTERFACE_OUT_UNICAST
from constants import INTERFACE_PHYSICAL_ADDRESS
from constants import INTERFACE_SPEED
from constants import INTERFACE_TYPE
from constants import LOCATION_KEY
from constants import MTU_KEY
from constants import OID_KEY
from constants import OPERATIONAL_STATUS_KEY
from constants import OPERATIONAL_STATUS_VALUES
from constants import OUT_DATA_KEY
from constants import OUT_DISCARDS_KEY
from constants import OUT_ERRORS_KEY
from constants import OUT_UNICAST_KEY
from constants import PORT
from constants import PRIVACY_PASS_PHRASE
from constants import PRIVACY_PROTOCOL
from constants import PRIVACY_PROTOCOLS
from constants import SNMP_V2
from constants import SNMP_V3
from constants import SPEED_KEY
from constants import SYSTEM_CONTACT
from constants import SYSTEM_DESC
from constants import SYSTEM_LOCATION
from constants import SYSTEM_NAME
from constants import SYSTEM_OBJECT_ID
from constants import SYSTEM_UPTIME
from constants import TYPE_KEY
from constants import TYPE_VALUES
from constants import UNICAST_KEY
from constants import UPTIME_KEY
from constants import USER
from pysnmp.smi.rfc1902 import ObjectIdentity
from pysnmp.smi.rfc1902 import ObjectType
from pysnmp_util import handle_errors
from pysnmp_util import SNMPClient

logger = logging.getLogger(__name__)


def get_adapter_definition() -> AdapterDefinition:
    with Timer(logger, "Get Adapter Definition"):
        definition = AdapterDefinition(ADAPTER_KIND, ADAPTER_NAME)
        definition.define_string_parameter(HOSTNAME, "Hostname")
        definition.define_int_parameter(PORT, "Port", default=161)

        snmp_v2 = definition.define_credential_type(SNMP_V2)
        snmp_v2.define_password_parameter(COMMUNITY_STRING, "Community String")
        snmp_v3 = definition.define_credential_type(SNMP_V3)
        snmp_v3.define_string_parameter(USER, "User")
        snmp_v3.define_enum_parameter(
            AUTH_PROTOCOL,
            label="Authentication Protocol",
            values=AUTH_PROTOCOLS.keys(),
            default="SHA",
        )
        snmp_v3.define_password_parameter(AUTH_PASS_PHRASE, "Authentication Passphrase")
        snmp_v3.define_enum_parameter(
            PRIVACY_PROTOCOL,
            label="Privacy Protocol",
            values=PRIVACY_PROTOCOLS.keys(),
            default="AES128",
        )
        snmp_v3.define_password_parameter(PRIVACY_PASS_PHRASE, "Privacy Passphrase")

        device = definition.define_object_type(DEVICE_OBJECT, "SNMP Device")
        device.define_string_property(DESCRIPTION_KEY, "Description")
        device.define_string_property(OID_KEY, "Object ID")
        device.define_numeric_property(UPTIME_KEY, "Uptime", unit=Units.TIME.DAYS)
        device.define_string_property(CONTACT_KEY, "Contact")
        device.define_string_property(LOCATION_KEY, "Location")

        interface = definition.define_object_type(INTERFACE_OBJECT, "Interface")
        interface.define_string_property(DESCRIPTION_KEY, "Description")
        interface.define_string_property(TYPE_KEY, "Type")
        interface.define_numeric_property(MTU_KEY, "MTU (octets)")
        interface.define_string_property(ADDRESS_KEY, "MAC Address")
        interface.define_string_property(ADMIN_STATUS_KEY, "Admin Status")
        interface.define_string_property(OPERATIONAL_STATUS_KEY, "Operational Status")
        interface.define_metric(
            SPEED_KEY, "Current Bandwidth", unit=Units.DATA_RATE.BIT_PER_SECOND
        )
        data_group = interface.define_instanced_group(DATA_GROUP, "Data")
        data_group.define_metric(DATA_KEY, "Total (octets)")
        data_group.define_metric(UNICAST_KEY, "Unicast", unit=Units.MISC.PACKETS)
        data_group.define_metric(DISCARDS_KEY, "Discards", unit=Units.MISC.PACKETS)
        data_group.define_metric(ERRORS_KEY, "Errors", unit=Units.MISC.PACKETS)

        logger.debug(f"Returning adapter definition: {definition.to_json()}")
        return definition


def test(adapter_instance: AdapterInstance) -> TestResult:
    with Timer(logger, "Test"):
        result = TestResult()
        try:
            client = SNMPClient(adapter_instance)

            iterator = client.get_command(
                ObjectType(ObjectIdentity(SYSTEM_NAME)),
            )

            for error_indication, error_status, error_index, var_binds in iterator:
                if handle_errors(
                    logger,
                    result,
                    error_indication,
                    error_status,
                    error_index,
                    var_binds,
                ):
                    continue
                for varBind in var_binds:  # SNMP response contents
                    logger.info(" = ".join([x.prettyPrint() for x in varBind]))

        except Exception as e:
            logger.error("Unexpected connection test error")
            logger.exception(e)
            result.with_error("Unexpected connection test error: " + repr(e))
        finally:
            logger.debug(f"Returning test result: {result.get_json()}")
            return result


def collect(adapter_instance: AdapterInstance) -> CollectResult:
    with Timer(logger, "Collection"):
        result = CollectResult()
        try:
            client = SNMPClient(adapter_instance)

            # Get some sample data from the SNMPv2-MIB. Most SNMP devices implement
            # this MIB. Omit index_count (or use index_count=0) to retrieve scalar data.
            for data, indices in client.get_OIDs(
                [
                    SYSTEM_DESC,
                    SYSTEM_OBJECT_ID,
                    SYSTEM_UPTIME,
                    SYSTEM_CONTACT,
                    SYSTEM_NAME,
                    SYSTEM_LOCATION,
                ],
                logger=logger,
                result=result,
            ):
                device = result.object(
                    ADAPTER_KIND, DEVICE_OBJECT, str(data[SYSTEM_NAME])
                )
                device.with_property(DESCRIPTION_KEY, str(data[SYSTEM_DESC]))
                device.with_property(OID_KEY, str(data[SYSTEM_OBJECT_ID]))
                device.with_property(UPTIME_KEY, int(data[SYSTEM_UPTIME] / 8640000.0))
                device.with_property(CONTACT_KEY, str(data[SYSTEM_CONTACT]))
                device.with_property(LOCATION_KEY, str(data[SYSTEM_LOCATION]))

            # Get some sample data from the IF-MIB. Most SNMP devices implement
            # this MIB. Use 'index_count=1' to get tabular data with one index.
            for data, indices in client.get_OIDs(
                [
                    INTERFACE_DESCRIPTION,
                    INTERFACE_TYPE,
                    INTERFACE_MTU,
                    INTERFACE_SPEED,
                    INTERFACE_PHYSICAL_ADDRESS,
                    INTERFACE_ADMIN_STATUS,
                    INTERFACE_OPERATIONAL_STATUS,
                    INTERFACE_IN_DATA,
                    INTERFACE_IN_UNICAST,
                    INTERFACE_IN_DISCARDS,
                    INTERFACE_IN_ERRORS,
                    INTERFACE_OUT_DATA,
                    INTERFACE_OUT_UNICAST,
                    INTERFACE_OUT_DISCARDS,
                    INTERFACE_OUT_ERRORS,
                ],
                index_count=1,
                logger=logger,
                result=result,
            ):
                if_id = f"IF-{str(indices[0])}"

                interface = result.object(ADAPTER_KIND, INTERFACE_OBJECT, if_id)
                device.add_child(interface)

                interface.with_property(
                    DESCRIPTION_KEY, str(data[INTERFACE_DESCRIPTION])
                )

                if_type = TYPE_VALUES.get(int(data[INTERFACE_TYPE]), "Unknown")
                interface.with_property(TYPE_KEY, if_type)
                interface.with_property(MTU_KEY, int(data[INTERFACE_MTU]))

                address = ":".join(
                    [f"{s:0x}" for s in data[INTERFACE_PHYSICAL_ADDRESS]]
                )
                interface.with_property(ADDRESS_KEY, address)

                admin_status = ADMIN_STATUS_VALUES.get(
                    int(data[INTERFACE_ADMIN_STATUS]), "Unknown"
                )
                interface.with_property(ADMIN_STATUS_KEY, admin_status)

                operational_status = OPERATIONAL_STATUS_VALUES.get(
                    int(data[INTERFACE_OPERATIONAL_STATUS]), "Unknown"
                )
                interface.with_property(OPERATIONAL_STATUS_KEY, operational_status)

                interface.with_metric(SPEED_KEY, int(data[INTERFACE_SPEED]))
                interface.with_metric(IN_DATA_KEY, int(data[INTERFACE_IN_DATA]))
                interface.with_metric(OUT_DATA_KEY, int(data[INTERFACE_OUT_DATA]))
                interface.with_metric(IN_UNICAST_KEY, int(data[INTERFACE_IN_UNICAST]))
                interface.with_metric(OUT_UNICAST_KEY, int(data[INTERFACE_OUT_UNICAST]))
                interface.with_metric(IN_DISCARDS_KEY, int(data[INTERFACE_IN_DISCARDS]))
                interface.with_metric(
                    OUT_DISCARDS_KEY, int(data[INTERFACE_OUT_DISCARDS])
                )
                interface.with_metric(IN_ERRORS_KEY, int(data[INTERFACE_IN_ERRORS]))
                interface.with_metric(OUT_ERRORS_KEY, int(data[INTERFACE_OUT_ERRORS]))

        except Exception as e:
            logger.error("Unexpected collection error")
            logger.exception(e)
            result.with_error("Unexpected collection error: " + repr(e))
        finally:
            logger.debug(f"Returning collection result {result.get_json()}")
            return result


def get_endpoints(adapter_instance: AdapterInstance) -> EndpointResult:
    # This is only relevant for HTTPS endpoints, so we can't use it for SNMP. Just
    # return an empty endpoint result.
    with Timer(logger, "Get Endpoints"):
        return EndpointResult()


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
