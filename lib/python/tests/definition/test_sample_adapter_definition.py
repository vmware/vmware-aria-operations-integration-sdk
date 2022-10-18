#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from aria.ops.definition.adapter_definition import AdapterDefinition
from aria.ops.definition.group import Group
from aria.ops.definition.units import Units
from pprint import pprint


def test_sample_adapter_definition():
    definition = AdapterDefinition("NSXALBAdapter", "NSX ALB (Avi)", "nsx_alb_adapter_instance", "NSX ALB Adapter Instance")
    credential = definition.define_credential_type("nsx_alb_credential", "NSX ALB Credential")
    credential.define_string_parameter("username", "Username")
    credential.define_password_parameter("password", "Password")

    definition.define_string_parameter("host", "NSX Adapter Instance Host")
    definition.define_int_parameter("timeout", "Connection Timeout", required=False, default=5)

    tenant = definition.define_object_type("tenant", "Tenant")
    tenant.define_string_identifier("uuid", "Tenant UUID")
    tenant.define_metric("clouds", "Number of Clouds")

    cloud = definition.define_object_type("cloud", "Cloud")
    cloud.define_string_identifier("uuid", "UUID")
    cloud.define_string_property("license_type", "License Type")
    cloud.define_metric("virtual_services", "Number of Virtual Services")

    service_engine_group = definition.define_object_type("service_engine_group", "Service Engine Group")
    service_engine_group.define_string_identifier("uuid", "UUID")
    service_engine_group.define_string_property("license_type", "License Type")
    service_engine_group.define_metric("service_engines", "Number of Service Engines")

    service_engine = definition.define_object_type("service_engine", "Service Engine")
    service_engine.define_string_identifier("uuid", "UUID")
    service_engine.define_string_property("controller_ip", "Controller IP")
    service_engine.define_metric("total_cpu_utilization", "Total CPU Usage", unit=Units.RATIO.PERCENT)
    service_engine.define_metric("total_memory", "Memory Capacity", unit=Units.DATA_SIZE.BIBYTE)
    service_engine.define_metric("free_memory", "Free Memory", unit=Units.DATA_SIZE.BIBYTE)
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
