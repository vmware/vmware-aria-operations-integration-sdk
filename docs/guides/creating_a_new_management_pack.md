# Creating a New Management Pack
* * * 

This guide assumes you have already set up the SDK and know how to create a new project.
It walks you through the steps necessary to monitor an endpoint, using Alibaba Cloud as
an example.

This section will create a simple management pack that creates objects with metrics,
properties, and relationships that monitors Alibaba Cloud. It assumes you have already
installed the SDK and understand the tools and steps in the 'Get Started' section. It
also assumes you have an Alibaba Cloud account.

For the purposes of this walkthrough, we will be adding an ECS Instance object with
six properties, and a relationship to the Adapter Instance. All the data can be found
by calling the `DescribeInstancesRequest` method in the ECS Python Library.

The first step is to run `mp-init` and create a new project. There are no restrictions,
except that the adapter kind key cannot be used by another management pack that is
installed on the same system. For example, we used the following to create the sample:

```
❯ mp-init
Enter a directory to create the project in. This is the directory where adapter code, metadata, and
content will reside. If the directory doesn't already exist, it will be created.
Path: alibaba-cloud-mp
Management pack display name: Alibaba Cloud
Management pack adapter key: AlibabaCloud
Management pack description: Sample Management Pack that monitors Alibaba Cloud
Management pack vendor: VMware, Inc
Enter a path to a EULA text file, or leave blank for no EULA:
Enter a path to the management pack icon file, or leave blank for no icon:
An icon can be added later by setting the 'pak_icon' key in 'manifest.txt' to the
icon file name and adding the icon file to the root project directory.
Creating Project [Finished]

project generation completed
```

The completed management pack is found in
[the 'samples' directory](https://github.com/vmware/vmware-aria-operations-integration-sdk/tree/main/samples/alibaba-cloud-mp), and can be used as a reference
for this walkthrough or as a starting point for creating your own.

Once the project finished generating, we can change directory into the project
and activate the Python virtual environment.

Next, we need to modify the adapter code. We will break this up into several steps:

  1. [Add a library for connecting to Alibaba](#add-a-library-for-connection-to-alibaba-cloud)
  2. [Modify the adapter definition to add fields for connecting to Alibaba Cloud](#modify-the-adapter-definition-to-add-fields-for-connecting-to-alibaba-cloud)
  3. [Modify the `test` method to create an Alibaba Cloud connection and run a query](#modify-the-test-method-to-create-an-alibaba-cloud-connection-and-run-a-query)
  4. [Modify the `collect` method to collect objects, metrics, properties, and
     relationships](#modify-the-collect-method-to-collect-objects-metrics-properties-and-relationships)
  5. [Verify the Alibaba Cloud MP](#verify-the-alibaba-cloud-mp)

#### Add a library for connection to Alibaba Cloud

In order to add the metrics we want, we will need to be able to send requests to Alibaba
Cloud. We could use any HTTP Rest library, such as `requests`, but it's usually easier
to use a library designed for the specific service we are monitoring. Thus, for this
sample we will use the official Alibaba Cloud SDK:
[`aliyun-python-sdk-core`](https://github.com/aliyun/aliyun-openapi-python-sdk).
Since we will be monitoring ECS instances, we will also need
[`aliyun-python-sdk-ecs`](https://github.com/aliyun/aliyun-openapi-python-sdk).

To add a library to the adapter, open the file `adapter_requirements.txt` and add a new
line with the name of the library. Optionally, we can also add a version constraint.
Here's what the modified file should look like:
```
vmware-aria-operations-integration-sdk-lib==0.7.*
psutil
aliyun-python-sdk-core==2.13.36
aliyun-python-sdk-ecs==4.24.61
```

> Note: We can also remove the `psutil` library, as that is only used in the sample code
> that we will be replacing. However, we would then no longer be able to run `mp-test`
> until we have removed the sample code that depends on `psutil`, so for now we will
> keep it.

#### Modify the adapter definition to add fields for connecting to Alibaba Cloud

Now that we have added the library, we need to see what information it needs in order
to connect. From the documentation, the client requires:
* Access Key ID
* Region ID
* Access Secret

In the `app/adapter.py` file, find the `get_adapter_definition()` method. We will define
parameters for the `Access Key ID` and `Region ID`, and a credential for the
`Access Key Secret`. We could put the `Access Key ID` in the credential, however
credentials are not used to identify adapter instances. If `Region ID` was the only
required parameter, then we would only be able to make one Adapter Instance per region.
Using the `Access Key ID` as an additional identifier will allow us to monitor multiple
accounts with the same `Region ID`.

After also removing the 'ID' parameter used by the sample adapter, the
method could look similar to this:

```python
def get_adapter_definition() -> AdapterDefinition:
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
            "us-west-1"
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

    # The key 'container_memory_limit' is a special key that is read by the VMware Aria Operations collector to
    # determine how much memory to allocate to the docker container running this adapter. It does not
    # need to be read inside the adapter code.
    definition.define_int_parameter(
        "container_memory_limit",
        label="Adapter Memory Limit (MB)",
        description="Sets the maximum amount of memory VMware Aria Operations can "
                    "allocate to the container running this adapter instance.",
        required=True,
        advanced=True,
        default=1024,
    )
```

Now that we've defined the connection parameters, we should define the objects that
we will collect. For now, let's collect some information about ECS Instances.
This is a small example. The implementation in the
[samples directory](https://github.com/vmware/vmware-aria-operations-integration-sdk/tree/main/samples/alibaba-cloud-mp) includes ECS Metrics and an additional
Security Group object type.

```python
    ecs_instance = definition.define_object_type("ecs_instance", "ECS Instance")
    ecs_instance.define_string_identifier("instance_id", "Instance ID")
    ecs_instance.define_string_identifier("region_id", "Region ID")
    ecs_instance.define_numeric_property("cpu", "CPU Count")
    ecs_instance.define_numeric_property("memory", "Total Memory", unit=Units.DATA_SIZE.MEBIBYTE)
    ecs_instance.define_string_property("status", "Status")
    ecs_instance.define_string_property("instance_type", "Instance Type")
    ecs_instance.define_string_property("private_ip", "Private IP Addresses")
    ecs_instance.define_string_property("public_ip", "Public IP Addresses")
```

#### Modify the `test` method to create an Alibaba Cloud connection and run a query

We can try to connect and run a test query. We will do this in the `test` method. Notice
this takes an `AdapterInstance` as a parameter. We will replace all the code that is
inside the try block.

All the parameters and credentials from the definition will be present in this Adapter
Instance. We can access them like this, using the `key`s that we defined in the
`get_adapter_definition` function to get the value assigned to that parameter:

```python
    access_key = adapter_instance.get_identifier_value("access_key_id")
    region = adapter_instance.get_identifier_value("region_id")
    secret = adapter_instance.get_credential_value("access_key_secret")
```

We can then use them to connect to Alibaba Cloud and run a test query. First import the
require modules:

```python
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
```
Then using the identifier values from above, create a client and initiate a request:
```python
    # Create and initialize a AcsClient instance
    client = AcsClient(
        access_key,
        secret,
        region,
    )

    request = DescribeInstancesRequest.DescribeInstancesRequest()
    request.set_accept_format('json')

    response = client.do_action_with_exception(request)

    logger.info(str(response, encoding='utf-8'))
    return result
```

Since we can expect that this will sometimes fail, e.g., if the user provides the wrong
Access Key or Secret, we should ensure there is good error-handling in this function.

If we detect a failure (e.g., in the `except` block), we should call
`result.with_error(error_message)` to indicate the test has failed. If no errors have
been attached to the `result` object, the test will pass. (Note that calling
`result.with_error(...)` multiple times in the same test will result in only the last
error being displayed.)

If the management pack will be widely distributed, it may also be worthwhile to catch
common errors and ensure the resulting messages are clear and user-friendly.

We should now be able to run `mp-test connect` to run this code. The `mp-test` tool
will ask you to create a new connection, prompting for 'Access Key ID', 'Region ID', and
'Access Key Secret'. After, it will ask if it should override SuiteAPI<sup>1</sup>
credentials. We will not need them for this sample, so we can select 'No'.

> <sup>1</sup>SuiteAPI is a REST API on VMware Aria Operations that can be used for many
> purposes. The documentation for this API can be found on any VMware Aria Operations
> instance at https://[aria_ops_hostname]/suite-api/. The 'adapter_instance' object that
> is passed to the 'test', 'get_endpoints', and 'collect' methods can automatically
> connect to this API and has methods for querying it.

If everything was successful, the result should look similar to this:
```
(venv-Alibaba Cloud) ❯ mp-test connect
Choose a connection:  default
Building adapter [Finished]
Waiting for adapter to start [Finished]
Running Connect [Finished]
{}

Avg CPU %                     | Avg Memory Usage %         | Memory Limit | Network I/O         | Block I/O
------------------------------+----------------------------+--------------+---------------------+--------------
29.6 % (0.0% / 29.6% / 59.1%) | 4.0 % (4.0% / 4.0% / 4.0%) | 1.0 GiB      | 5.52 KiB / 8.76 KiB | 0.0 B / 0.0 B

Request completed in 1.24 seconds.

All validation logs written to '~/Code/alibaba-cloud-mp/logs/validation.log'
Validation passed with no errors
```

#### Modify the `collect` method to collect objects, metrics, properties, and relationships

Now that the `test` method is working, we can implement the `collect` method. This is
the method where we query Alibaba Cloud for the objects, metrics, etc, we want and send
them to VMware Aria Operations.

First, we should remove all the sample code inside the `try` block. All the code for the
following steps should be inside the `try` block.

Then, we need to establish a connection to Alibaba Cloud. We can do this in the same way
as in test connect. In many cases creating a function for connecting that is called from
both `test` and `collect` is worthwhile.

Next, we'll run several queries to get the data from Alibaba Cloud that we want, add
the objects to the `result`, add data to the objects, and return the result. This
collects all the properties in the small definition above. The implementation in the
[samples directory](https://github.com/vmware/vmware-aria-operations-integration-sdk/tree/main/samples/alibaba-cloud-mp) has more data.


```python
    request = DescribeInstancesRequest.DescribeInstancesRequest()
    request.set_accept_format('json')

    response = client.do_action_with_exception(request)
    json_response = json.loads(response)

    # Add the adapter instance so that we can make a relationship to it from the
    # ECS instances
    result.add_object(adapter_instance)

    for instance in json_response.get("Instances", {}).get("Instance", []):
        id = instance.get("InstanceId")
        if not id:
            continue
        name = instance.get("HostName", id)

        ecs_object = result.object(ADAPTER_KIND, "ecs_instance", name,
                      identifiers=[Identifier("instance_id", id),
                                   Identifier("region_id", region)])

        ecs_object.add_parent(adapter_instance)

        ecs_object.with_property("cpu", instance.get("Cpu"))
        ecs_object.with_property("memory", instance.get("Memory"))
        ecs_object.with_property("status", instance.get("Status"))
        ecs_object.with_property("instance_type", instance.get("InstanceType"))
        ecs_object.with_property("private_ip", str(instance.get("VpcAttributes", {}).get("PrivateIpAddress", {}).get("IpAddress", [])))
        ecs_object.with_property("public_ip", str(instance.get("PublicIpAddress", {}).get("IpAddress", [])))
```

#### Verify the Alibaba Cloud MP

To verify the MP, run `mp-test collect` using the same connection we created earlier. We
should see all ECS Instances that are present in the selected region that the RAM user
associated with the access key has permission to view, with a small number of properties
attached to it. In addition, each ECS Instance should be a child of the Adapter
Instance. For example, with a very small environment with a single ECS Instance, we may
see a result similar to this:
```
(venv-Alibaba Cloud) ❯ mp-test -c default collect
Building adapter [Finished]
Waiting for adapter to start [Finished]
Running Collect [Finished]
{
    "nonExistingObjects": [],
    "relationships": [],
    "result": [
        {
            "events": [],
            "key": {
                "adapterKind": "AlibabaCloud",
                "identifiers": [
                    {
                        "isPartOfUniqueness": true,
                        "key": "access_key_id",
                        "value": "LTAI5tJAcgHHoDT9d4xWNQBu"
                    },
                    {
                        "isPartOfUniqueness": false,
                        "key": "container_memory_limit",
                        "value": "1024"
                    },
                    {
                        "isPartOfUniqueness": true,
                        "key": "region_id",
                        "value": "us-east-1"
                    }
                ],
                "name": "default",
                "objectKind": "AlibabaCloud_adapter_instance"
            },
            "metrics": [],
            "properties": []
        },
        {
            "events": [],
            "key": {
                "adapterKind": "AlibabaCloud",
                "identifiers": [
                    {
                        "isPartOfUniqueness": true,
                        "key": "instance_id",
                        "value": "i-0xi23s0o5pgnbdir3e3j"
                    },
                    {
                        "isPartOfUniqueness": true,
                        "key": "region_id",
                        "value": "us-east-1"
                    }
                ],
                "name": "iZ0xi23s0o5pgnbdir3e3jZ",
                "objectKind": "ecs_instance"
            },
            "metrics": [],
            "properties": [
                {
                    "key": "cpu",
                    "numberValue": 1.0,
                    "timestamp": 1681933134430
                },
                {
                    "key": "memory",
                    "numberValue": 1024.0,
                    "timestamp": 1681933134430
                },
                {
                    "key": "status",
                    "stringValue": "Running",
                    "timestamp": 1681933134430
                },
                {
                    "key": "instance_type",
                    "stringValue": "ecs.n1.tiny",
                    "timestamp": 1681933134430
                },
                {
                    "key": "private_ip",
                    "stringValue": "['172.29.43.26']",
                    "timestamp": 1681933134430
                },
                {
                    "key": "public_ip",
                    "stringValue": "['47.90.216.22']",
                    "timestamp": 1681933134430
                }
            ]
        }
    ]
}
Collection summary:

Table cell format is: 'total (min/median/max)'

Object Type                                 | Count | Metrics | Properties | Events | Parents | Children
--------------------------------------------+-------+---------+------------+--------+---------+---------
AlibabaCloud::AlibabaCloud_adapter_instance | 1     | 0       | 0          | 0      | 0       | 0
AlibabaCloud::ecs_instance                  | 1     | 0       | 6          | 0      | 0       | 0

Parent Type | Child Type | Count
------------+------------+------


Avg CPU %                     | Avg Memory Usage %         | Memory Limit | Network I/O          | Block I/O
------------------------------+----------------------------+--------------+----------------------+--------------
34.6 % (0.0% / 34.6% / 69.1%) | 4.0 % (4.0% / 4.0% / 4.0%) | 1.0 GiB      | 5.52 KiB / 10.21 KiB | 0.0 B / 0.0 B

Collection completed in 0.96 seconds.

All validation logs written to '~/Code/alibaba-cloud-mp/logs/validation.log'
Validation passed with no errors
```

When everything is working as expected locally using `mp-test`, we can run
`mp-build` and install on VMware Aria Operations for a final verification.


#### Next Steps

* [Adding to an Adapter](adding_to_an_adapter.md)
    * [Defining an Adapter and Adapter Instance in the Object Model](adding_to_an_adapter.md#defining-an-adapter-and-adapter-instance-in-the-object-model)
    * [Adding a Configuration Field to an Adapter Instance](adding_to_an_adapter.md#adding-a-configuration-field-to-an-adapter-instance-in-the-object-model)
    * [Defining a Credential in the Object Model](adding_to_an_adapter.md#defining-a-credential-in-the-object-model)
    * [Creating an Adapter Instance](adding_to_an_adapter.md#creating-an-adapter-instance)
    * [Adding an Object Type to the Object Model](adding_to_an_adapter.md#adding-an-object-type-to-the-object-model)
    * [Creating an Object](adding_to_an_adapter.md#creating-an-object)
    * [Defining an Attribute in the Object Model](adding_to_an_adapter.md#defining-an-attribute-in-the-object-model)
    * [Creating a Metric or Property](adding_to_an_adapter.md#creating-a-metric-or-property)
    * [Creating an Event](adding_to_an_adapter.md#creating-an-event)
    * [Creating a Relationship](adding_to_an_adapter.md#creating-a-relationship)
* [Adding Content](adding_content.md)
    * [Adding a Dashboard](adding_content.md#adding-a-dashboard)
    * [Adding a Report Template](adding_content.md#adding-a-report-template)
    * [Adding Alert Definitions](adding_content.md#adding-alert-definitions)
    * [Adding a Traversal](adding_content.md#adding-a-traversal)
    * [Adding Localization](adding_content.md#adding-localization)


