#  Copyright 2022-2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import json
import sys
import time
from typing import List
from typing import Optional

import aria.ops.adapter_logging as logging
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526 import DescribeSecurityGroupsRequest
from aria.ops.adapter_instance import AdapterInstance
from aria.ops.definition.adapter_definition import AdapterDefinition
from aria.ops.definition.units import Units
from aria.ops.object import Identifier
from aria.ops.result import CollectResult
from aria.ops.result import EndpointResult
from aria.ops.result import TestResult
from aria.ops.timer import Timer
from constants import ADAPTER_KIND
from constants import ADAPTER_NAME
from constants import ECS_OBJECT_TYPE
from constants import SECURITY_GROUP_OBJECT_TYPE

logger = logging.getLogger(__name__)


def test(adapter_instance: AdapterInstance) -> TestResult:
    with Timer(logger, "Test"):
        result = TestResult()
        try:
            access_key = adapter_instance.get_identifier_value("access_key_id")
            region = adapter_instance.get_identifier_value("region_id")
            secret = adapter_instance.get_credential_value("access_key_secret")

            # Create and initialize a AcsClient instance
            client = AcsClient(
                access_key,
                secret,
                region,
            )

            request = DescribeInstancesRequest.DescribeInstancesRequest()
            request.set_accept_format("json")

            response = client.do_action_with_exception(request)
            logger.debug(str(response, encoding="utf-8"))
        except ClientException as e:
            logger.error("Encountered a ClientException during test connect")
            logger.exception(e)
            result.with_error(e.error_message)
        except ServerException as e:
            logger.error("Encountered a ServerException during test connect")
            logger.exception(e)
            result.with_error(e.error_message)
        finally:
            logger.debug(f"Returning test result: {result.get_json()}")
            return result


def get_endpoints(adapter_instance: AdapterInstance) -> EndpointResult:
    # The Alibaba Cloud library is handling certificates.
    return EndpointResult()


def collect(adapter_instance: AdapterInstance) -> CollectResult:
    with Timer(logger, "Collect"):
        result = CollectResult()
        try:
            access_key = adapter_instance.get_identifier_value("access_key_id")
            region = adapter_instance.get_identifier_value("region_id")
            secret = adapter_instance.get_credential_value("access_key_secret")

            # Create and initialize a AcsClient instance
            client = AcsClient(
                access_key,
                secret,
                region,
            )

            # Add the adapter instance to the CollectResult, so we can make
            # relationships to it from Security Groups and ECS Instances
            result.add_object(adapter_instance)

            collect_security_groups(adapter_instance, client, result)
            collect_ecs_instances(adapter_instance, client, result)

        except ClientException as e:
            logger.error("Encountered a ClientException during collect")
            logger.exception(e)
            result.with_error(e.error_message)
        except ServerException as e:
            logger.error("Encountered a ServerException during collect")
            logger.exception(e)
            result.with_error(e.error_message)
        except Exception as e:
            logger.error("Unexpected collection error")
            logger.exception(e)
            result.with_error("Unexpected collection error: " + repr(e))
        finally:
            logger.debug(f"Returning collection result {result.get_json()}")
            return result


def collect_security_groups(
    adapter_instance: AdapterInstance, client: AcsClient, result: CollectResult
) -> None:
    """
    Collect information about every Security Group for the given Region and Access Key
    from the client

    :param adapter_instance: Adapter instance object from the 'collect' method
    :param client: Authenticated AcsClient for connecting to Alibaba Cloud
    :param result: CollectResult that is returned by the 'collect' method
    :return: None
    """
    with Timer(logger, "Collect Security Groups"):
        security_groups_request = (
            DescribeSecurityGroupsRequest.DescribeSecurityGroupsRequest()
        )
        security_groups_request.set_accept_format("json")

        security_groups = json.loads(
            client.do_action_with_exception(security_groups_request)
        )
        for security_group in security_groups.get("SecurityGroups", {}).get(
            "SecurityGroup", []
        ):
            security_group_id = security_group.get("SecurityGroupId")
            if not security_group_id:
                continue
            name = security_group.get("SecurityGroupName", security_group_id)
            security_group_object = result.object(
                ADAPTER_KIND,
                SECURITY_GROUP_OBJECT_TYPE,
                name,
                [Identifier("security_group_id", security_group_id)],
            )

            security_group_object.add_parent(adapter_instance)

            security_group_object.with_property(
                "service_managed", str(bool(security_group.get("ServiceManaged")))
            )
            security_group_object.with_property(
                "type", security_group.get("SecurityGroupType")
            )


def collect_ecs_instances(
    adapter_instance: AdapterInstance, client: AcsClient, result: CollectResult
) -> None:
    """
    Collect information about every ECS Instance for the given Region and Access Key
    from the client

    :param adapter_instance: Adapter instance object from the 'collect' method
    :param client: Authenticated AcsClient for connecting to Alibaba Cloud
    :param result: CollectResult that is returned by the 'collect' method
    :return: None
    """
    with Timer(logger, "Collect ECS Instances"):
        ecs_instances_request = DescribeInstancesRequest.DescribeInstancesRequest()
        ecs_instances_request.set_accept_format("json")

        instances = json.loads(client.do_action_with_exception(ecs_instances_request))
        for instance in instances.get("Instances", {}).get("Instance", []):
            instance_id = instance.get("InstanceId")
            if not instance_id:
                continue
            name = instance.get("HostName", instance_id)
            region = adapter_instance.get_identifier_value("region_id")

            # Create the ECS object
            ecs_object = result.object(
                ADAPTER_KIND,
                ECS_OBJECT_TYPE,
                name,
                identifiers=[
                    Identifier("instance_id", instance_id),
                    Identifier("region_id", region),
                ],
            )

            ecs_object.add_parent(adapter_instance)

            # Collect properties from the 'DescribeInstanceRequest' endpoint
            ecs_object.with_property("cpu", instance.get("Cpu"))
            ecs_object.with_property("memory", instance.get("Memory"))
            ecs_object.with_property("status", instance.get("Status"))
            ecs_object.with_property("instance_type", instance.get("InstanceType"))
            ecs_object.with_property(
                "private_ip",
                str(
                    instance.get("VpcAttributes", {})
                    .get("PrivateIpAddress", {})
                    .get("IpAddress", [])
                ),
            )
            ecs_object.with_property(
                "public_ip",
                str(instance.get("PublicIpAddress", {}).get("IpAddress", [])),
            )

            security_group_ids = instance.get("SecurityGroupIds", {}).get(
                "SecurityGroupId", []
            )

            # Access security group object and add a relationship to the ECS Instance
            for security_group_id in security_group_ids:
                security_group = result.object(
                    ADAPTER_KIND,
                    SECURITY_GROUP_OBJECT_TYPE,
                    security_group_id,
                    [Identifier("security_group_id", security_group_id)],
                )
                security_group.add_child(ecs_object)

            # Collect additional metrics if available
            # Make sure Host Monitoring is enabled in Cloud Monitor
            with Timer(logger, f"Collect ECS Instance Metrics for {name}"):
                cpu_usage_average = get_metric_average_over_period(
                    client, instance_id, "CPUUtilization"
                )
                if cpu_usage_average:
                    ecs_object.with_metric("cpu_usage_average", cpu_usage_average)

                memory_free_usage_average = get_metric_average_over_period(
                    client, instance_id, "memory_freeutilization"
                )
                if memory_free_usage_average:
                    ecs_object.with_metric(
                        "memory_usage_average", 100 - memory_free_usage_average
                    )


def get_metric_average_over_period(
    client: AcsClient, instance_id: str, metric_name: str, period_duration: int = 60
) -> Optional[float]:
    """
    Returns the average value of a given metric on a given ECS Instance over a set
    period (default period is 1 hour).

    :param client: Authenticated AcsClient for connecting to Alibaba Cloud
    :param instance_id: The ECS Instance ID the metric describes
    :param metric_name: The name of the metric. A list can be found here:
           https://cms.console.aliyun.com/metric-meta/acs_ecs_dashboard/ecs?spm=a2c63.p38356.0.0.5a855c58bdtyCX
    :param period_duration: duration is in minutes, and is the period of time before
           present to compute the average over
    :return: floating point value representing the metric value, or None if a value
             could not be computed.
    """
    start_time = time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - period_duration * 60)
    )
    end_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    request = CommonRequest()
    request.set_accept_format("json")
    request.set_domain("metrics.aliyuncs.com")
    request.set_version("2019-01-01")
    request.set_action_name("DescribeMetricLast")
    request.add_query_param("Namespace", "acs_ecs_dashboard")
    request.add_query_param("MetricName", metric_name)
    request.add_query_param("StartTime", start_time)
    request.add_query_param("EndTime", end_time)
    request.add_query_param("Dimensions", '{"instanceId":"' + instance_id + '"}')
    request.add_query_param("Period", period_duration)

    try:
        response = client.do_action_with_exception(request)
        response_json = json.loads(response)
        datapoints = response_json.get("Datapoints", [])
        return float(json.loads(datapoints)[-1].get("Average", None))
    except Exception as e:
        logger.warning(
            f"Encountered an exception during collect when retrieving {metric_name} on instance {instance_id}"
        )
        logger.exception(e)
    return None


def get_adapter_definition() -> AdapterDefinition:
    """
    The adapter definition defines the object types and attribute types
    (metric/property) that are present in a collection. Setting these object types and
    attribute types helps VMware Aria Operations to validate, process, and display the
    data correctly.
    :return: AdapterDefinition
    """
    with Timer(logger, "Get Adapter Definition"):
        definition = AdapterDefinition(ADAPTER_KIND, ADAPTER_NAME)

        definition.define_string_parameter(
            "access_key_id",
            label="Access Key ID",
            description="The AccessKey ID of the RAM account",
            required=True,
        )
        definition.define_enum_parameter(
            "region_id",
            label="Region ID",
            values=[
                "cn-hangzhou",
                "cn-beijing",
                "cn-zhagjiakou",
                "cn-shanghai",
                "cn-qingdao",
                "cn-huhehaote",
                "cn-shenzhen",
                "cn-chengdu",
                "cn-hongkong",
                "ap-northeast-1",
                "ap-south-1",
                "ap-southeast-1",
                "ap-southeast-2",
                "ap-southeast-3",
                "ap-southeast-5",
                "eu-central-1",
                "eu-west-1",
                "me-east-1",
                "us-east-1",
                "us-west-1",
            ],
            description="Set the region to collect from. Only one region can be "
            "selected per Adapter Instance.",
            required=True,
        )
        ram_account = definition.define_credential_type("RAM Account")
        ram_account.define_password_parameter(
            "access_key_secret",
            "AccessKey Secret",
            required=True,
        )

        # The key 'container_memory_limit' is a special key that is read by the VMware
        # Aria Operations collector to determine how much memory to allocate to the
        # container running this adapter. It does not need to be read inside the
        # adapter code.
        definition.define_int_parameter(
            "container_memory_limit",
            label="Adapter Memory Limit (MB)",
            description="Sets the maximum amount of memory VMware Aria Operations can "
            "allocate to the container running this adapter instance.",
            required=True,
            advanced=True,
            default=1024,
        )

        security_group = definition.define_object_type(
            SECURITY_GROUP_OBJECT_TYPE, "Security Group"
        )
        security_group.define_string_identifier(
            "security_group_id", "Security Group ID"
        )
        security_group.define_string_property("service_managed", "Service Managed")
        security_group.define_string_property("type", "Type")

        ecs_instance = definition.define_object_type(ECS_OBJECT_TYPE, "ECS Instance")
        ecs_instance.define_string_identifier("instance_id", "Instance ID")
        ecs_instance.define_string_identifier("region_id", "Region ID")
        ecs_instance.define_numeric_property("cpu", "CPU Count")
        ecs_instance.define_numeric_property(
            "memory", "Total Memory", unit=Units.DATA_SIZE.MEBIBYTE
        )
        ecs_instance.define_string_property("status", "Status")
        ecs_instance.define_string_property("instance_type", "Instance Type")
        ecs_instance.define_string_property("private_ip", "Private IP Addresses")
        ecs_instance.define_string_property("public_ip", "Public IP Addresses")

        ecs_instance.define_metric(
            "cpu_usage_average", "Average CPU Usage", unit=Units.RATIO.PERCENT
        )
        ecs_instance.define_metric("memory_usage_average", unit=Units.RATIO.PERCENT)

        logger.debug(f"Returning adapter definition: {definition.to_json()}")
        return definition


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
