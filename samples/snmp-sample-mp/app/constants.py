#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from pysnmp.hlapi import *

ADAPTER_KIND = "SNMP_Sample"
ADAPTER_NAME = "SNMP Sample Adapter"

SNMP_V2 = "snmp_v2"
SNMP_V3 = "snmp_v3"

# Identifiers:
HOSTNAME = "hostname"
PORT = "port"

# V2C Credentials
COMMUNITY_STRING = "community_string"

# V3 Credentials
USER = "user"

AUTH_PROTOCOL = "authentication_protocol"
AUTH_PROTOCOLS = {
    "SHA": usmHMACSHAAuthProtocol,
    "MD5": usmHMACMD5AuthProtocol,
}
AUTH_PASS_PHRASE = "authentication_pass_phrase"

PRIVACY_PROTOCOL = "privacy_protocol"
PRIVACY_PROTOCOLS = {
    "DES": usmDESPrivProtocol,
    "3DES": usm3DESEDEPrivProtocol,
    "AES128": usmAesCfb128Protocol,
    "AES192": usmAesCfb192Protocol,
    "AES256": usmAesCfb256Protocol,
}
PRIVACY_PASS_PHRASE = "privacy_pass_phrase"


DEVICE = "device"

SYSTEM = "1.3.6.1.2.1.1"

DESCRIPTION_KEY = "description"
SYSTEM_DESC = f"{SYSTEM}.1.0"

OID_KEY = "oid"
SYSTEM_OBJECT_ID = f"{SYSTEM}.2.0"

UPTIME_KEY = "uptime"
SYSTEM_UPTIME = f"{SYSTEM}.3.0"

CONTACT_KEY = "contact"
SYSTEM_CONTACT = f"{SYSTEM}.4.0"

SYSTEM_NAME = f"{SYSTEM}.5.0"

LOCATION_KEY = "location"
SYSTEM_LOCATION = f"{SYSTEM}.6.0"
