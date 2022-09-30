#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from vrops.definition.adapter_definition import AdapterDefinition
from vrops.definition.units import *
from pprint import pprint

def test_sample_adapter_definition():
    definition = AdapterDefinition("NSXALBAdapter", "NSX ALB (Avi)", "nsx_alb_adapter_instance", "NSX ALB Adapter Instance")
    credential = definition.credential("nsx_alb_credential", "NSX ALB Credential")
    credential.string_credential_parameter("username", "Username")
    credential.password_credential_parameter("password", "Password")

    definition.string_parameter("host", "NSX Adapter Instance Host")
    definition.int_parameter("timeout", "Connection Timeout", required=False, default=5)

    tenant = definition.object_type("tenant", "Tenant")
    tenant.string_identifier("uuid", "Tenant UUID")
    tenant.metric("clouds", "Number of Clouds")

    cloud = definition.object_type("cloud", "Cloud")
    cloud.string_identifier("uuid", "UUID")
    cloud.string_property("license_type", "License Type")
    cloud.metric("virtual_services", "Number of Virtual Services")

    service_engine_group = definition.object_type("service_engine_group", "Service Engine Group")
    service_engine_group.string_identifier("uuid", "UUID")
    service_engine_group.string_property("license_type", "License Type")
    service_engine_group.metric("service_engines", "Number of Service Engines")

    service_engine = definition.object_type("service_engine", "Service Engine")
    service_engine.string_identifier("uuid", "UUID")
    service_engine.string_property("controller_ip", "Controller IP")
    service_engine.metric("total_cpu_utilization", "Total CPU Usage", unit=Units.RATIO.PERCENT)
    service_engine.metric("total_memory", "Memory Capacity", unit=Units.DATA_SIZE.BIBYTE)
    service_engine.metric("free_memory", "Free Memory", unit=Units.DATA_SIZE.BIBYTE)
    service_engine.add_group(packet_group())

    virtual_service = definition.define_object_type("virtual_service", "Virtual Service")
    virtual_service.define_string_identifier("uuid", "UUID")
    virtual_service.define_string_property("cloud_ref", "Parent Cloud")
    virtual_service.define_string_property("se_uuid", "Parent Service Engine")
    virtual_service.add_group(packet_group())
    data = virtual_service.define_group("data", "Data")
    data.define_metric("data_received", "Data Received", unit=Units.DATA_SIZE.BYTE)
    data.define_metric("data_sent", "Data Sent", unit=Units.DATA_SIZE.BYTE)

    pprint(definition.to_json())


def packet_group():
    packets = Group("packets", "Packets")
    packets.define_metric("total_packets_received", "Total Packets Received", unit=Units.MISC.PACKETS)
    packets.define_metric("total_packets_sent", "Total Packets Sent", unit=Units.MISC.PACKETS)
    return packets
