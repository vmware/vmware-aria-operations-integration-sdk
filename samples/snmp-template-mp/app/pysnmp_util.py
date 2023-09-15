#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from logging import Logger
from typing import Any
from typing import Generator
from typing import Iterator
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
from pysnmp.hlapi import CommunityData
from pysnmp.hlapi import ContextData
from pysnmp.hlapi import getCmd
from pysnmp.hlapi import nextCmd
from pysnmp.hlapi import SnmpEngine
from pysnmp.hlapi import UdpTransportTarget
from pysnmp.hlapi import usmAesCfb128Protocol
from pysnmp.hlapi import usmHMACSHAAuthProtocol
from pysnmp.hlapi import UsmUserData
from pysnmp.smi.rfc1902 import ObjectIdentity
from pysnmp.smi.rfc1902 import ObjectType


class SNMPClient:
    def __init__(self, adapter_instance: AdapterInstance) -> None:
        self._hostname = adapter_instance.get_identifier_value(HOSTNAME)
        self._port = int(adapter_instance.get_identifier_value(PORT))
        self._user_data = get_user_data(adapter_instance)

    def get_command(self, *var_binds: Any, **kwargs: Any) -> Iterator:
        return getCmd(  # type: ignore
            SnmpEngine(),
            self._user_data,
            UdpTransportTarget((self._hostname, self._port)),
            ContextData(),
            *var_binds,
            **kwargs,
        )

    def next_command(self, *var_binds: Any, **kwargs: Any) -> Iterator:
        return nextCmd(  # type: ignore
            SnmpEngine(),
            self._user_data,
            UdpTransportTarget((self._hostname, self._port)),
            ContextData(),
            *var_binds,
            **kwargs,
        )

    def get_OIDs(
        self,
        oids: list[str],
        index_count: int = 0,
        logger: Optional[Logger] = None,
        result: Optional[Union[CollectResult, TestResult]] = None,
        **kwargs: Any,
    ) -> Generator[tuple[dict[str, Any], tuple[str, ...]], None, None]:
        var_binds = [ObjectType(ObjectIdentity(oid)) for oid in oids]
        # Looking up the MIB gets more metadata about the OID we are passing in
        # (and allows querying by name instead of OID), but the number of
        # built-in MIBS in PySNMP is limited. Since we don't need them, we'll
        # disable this feature by default.
        kwargs.setdefault("lookupMib", False)
        kwargs.setdefault("lexicographicMode", False)

        def get_oid_and_index(key: str) -> tuple[str, tuple[str, ...]]:
            oid, *indices_list = str(key).rsplit(".", index_count)
            return oid, tuple(indices_list)

        if index_count == 0:
            iterator = self.get_command(*var_binds, **kwargs)
        else:
            iterator = self.next_command(*var_binds, **kwargs)
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

            # data = {key: value for (key, value) in var_binds}
            data = {}
            indices: tuple[str, ...] = ()
            for key, value in var_binds:
                oid, indices = get_oid_and_index(key)
                data[oid] = value
            if logger:
                logger.debug(data)
            yield data, indices


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
    else:
        raise Exception(f"Unknown credential type: {adapter_instance.credential_type}")


def handle_errors(
    logger: Optional[Logger],
    result: Optional[Union[CollectResult, TestResult]],
    error_indication: Any,
    error_status: Any,
    error_index: Any,
    var_binds: Any,
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
