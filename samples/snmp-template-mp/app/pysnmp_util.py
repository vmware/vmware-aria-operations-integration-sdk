#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from logging import Logger
from typing import Optional
from typing import Union

from aria.ops.adapter_instance import AdapterInstance
from aria.ops.result import CollectResult
from aria.ops.result import TestResult
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
from constants import USER
from pysnmp.hlapi import *


class SNMPClient:
    def __init__(self, adapter_instance):
        self._hostname = adapter_instance.get_identifier_value(HOSTNAME)
        self._port = int(adapter_instance.get_identifier_value(PORT))
        self._user_data = get_user_data(adapter_instance)

    def get_command(self, *var_binds, **kwargs):
        return getCmd(
            SnmpEngine(),
            self._user_data,
            UdpTransportTarget((self._hostname, self._port)),
            ContextData(),
            *var_binds,
            **kwargs,
        )

    def next_command(self, *var_binds, **kwargs):
        return nextCmd(
            SnmpEngine(),
            self._user_data,
            UdpTransportTarget((self._hostname, self._port)),
            ContextData(),
            *var_binds,
            **kwargs,
        )


def get_user_data(
    adapter_instance: AdapterInstance,
) -> Union[CommunityData, UsmUserData]:
    if adapter_instance.credential_type == SNMP_V2:
        community_string = adapter_instance.get_credential_value(COMMUNITY_STRING)
        return CommunityData(community_string)
    elif adapter_instance.credential_type == SNMP_V3:
        user = adapter_instance.get_credential_value(USER)

        auth_protocol_type = adapter_instance.get_credential_value(AUTH_PROTOCOL)
        auth_protocol = AUTH_PROTOCOLS.get(auth_protocol_type, usmHMACSHAAuthProtocol)
        auth_passphrase = adapter_instance.get_credential_value(AUTH_PASS_PHRASE)

        privacy_protocol_type = adapter_instance.get_credential_value(PRIVACY_PROTOCOL)
        privacy_protocol = PRIVACY_PROTOCOLS.get(
            privacy_protocol_type, usmAesCfb128Protocol
        )
        privacy_passphrase = adapter_instance.get_credential_value(PRIVACY_PASS_PHRASE)

        return UsmUserData(
            user,
            authProtocol=auth_protocol,
            authKey=auth_passphrase,
            privProtocol=privacy_protocol,
            privKey=privacy_passphrase,
        )


def handle_errors(
    logger: Optional[Logger],
    result: Optional[Union[CollectResult, TestResult]],
    error_indication,
    error_status,
    error_index,
    var_binds,
) -> bool:
    if error_indication:  # SNMP engine errors
        if logger:
            logger.warning(str(error_indication))
        if result:
            result.with_error(str(error_indication))
        return True
    else:
        if error_status:  # SNMP agent errors
            message = f"{error_status.prettyPrint()} at {var_binds[int(error_index) - 1] if error_index else '?'}"
            if logger:
                logger.warning(message)
            if result:
                result.with_error(message)
            return True
    return False
