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
from constants import AUTH_PASS_PHRASE
from constants import AUTH_PROTOCOL
from constants import AUTH_PROTOCOLS
from constants import COMMUNITY_STRING
from constants import HOSTNAME
from constants import PORT
from constants import PRIVACY_PASS_PHRASE
from constants import PRIVACY_PROTOCOL
from constants import PRIVACY_PROTOCOLS
from constants import SNMP_V2
from constants import SNMP_V3
from constants import SYSTEM_CONTACT
from constants import SYSTEM_DESC
from constants import SYSTEM_LOCATION
from constants import SYSTEM_NAME
from constants import SYSTEM_OBJECT_ID
from constants import SYSTEM_UPTIME
from constants import USER
from pysnmp.hlapi import *
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

        device = definition.define_object_type("device", "SNMP Device")
        device.define_string_property("description", "Description")
        device.define_string_property("oid", "Object ID")
        device.define_numeric_property("uptime", "Uptime", unit=Units.TIME.DAYS)
        device.define_string_property("contact", "Contact")
        device.define_string_property("location", "Location")

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
            # this MIB.
            iterator = client.get_command(
                ObjectType(ObjectIdentity(SYSTEM_DESC)),
                ObjectType(ObjectIdentity(SYSTEM_OBJECT_ID)),
                ObjectType(ObjectIdentity(SYSTEM_UPTIME)),
                ObjectType(ObjectIdentity(SYSTEM_CONTACT)),
                ObjectType(ObjectIdentity(SYSTEM_NAME)),
                ObjectType(ObjectIdentity(SYSTEM_LOCATION)),
                # Looking up the MIB gets more metadata about the OID we are passing in
                # (and allows querying by name instead of OID), but the number of
                # built-in MIBS in PySNMP is limited. Since we don't need them, we'll
                # disable this feature.
                lookupMib=False,
            )

            # For a 'get' command, there should be only one item in the iterator.
            for error_indication, error_status, error_index, var_binds in iterator:
                if handle_errors(
                    logger,
                    result,
                    error_indication,
                    error_status,
                    error_index,
                    var_binds,
                ):
                    # If we got an error, log and continue
                    continue

                # Build a dictionary from the result for easier processing
                data = {str(key): value for (key, value) in var_binds}

                if SYSTEM_NAME in data:
                    device = result.object(
                        ADAPTER_KIND, "device", str(data[SYSTEM_NAME])
                    )
                    device.with_property("description", str(data[SYSTEM_DESC]))
                    device.with_property("oid", str(data[SYSTEM_OBJECT_ID]))
                    device.with_property("uptime", int(data[SYSTEM_UPTIME] / 8640000.0))
                    device.with_property("contact", str(data[SYSTEM_CONTACT]))
                    device.with_property("location", str(data[SYSTEM_LOCATION]))

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
