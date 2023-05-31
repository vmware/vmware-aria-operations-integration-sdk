
## Walkthroughs

### Creating a New Management Pack
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
[the 'samples' directory](samples/alibaba-cloud-mp), and can be used as a reference
for this walkthrough or as a starting point for creating your own.

Once the project finished generating, we can change directory into the project
and activate the Python virtual environment.

Next, we need to modify the adapter code. We will break this up into several steps:

  1. [Add a library for connecting to Alibaba](#add-a-library-for-connection-to-alibaba-cloud)
  2. [Modify the adapter definition to add fields for connecting to Alibaba Cloud](#modify-the-adapter-definition-to-add-fields-for-connecting-to-alibaba-cloud)
  3. [Modify the `test` method to create an Alibaba Cloud connection and run a query](#modify-the-test-method-to-create-an-alibaba-could-connection-and-run-a-query)
  4. [Modify the `collect` method to collect objects, metrics, properties, and
     relationships](#modify-the-collect-method-to-collect-objects--metrics--properties--and-relationships)
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
[samples directory](samples/alibaba-cloud-mp) includes ECS Metrics and an additional
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
[samples directory](samples/alibaba-cloud-mp) has more data.


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
    * [Defining an Adapter](adding_to_an_adapter.md#defining-an-adapter)
    * [Defining an Adapter Instance](adding_to_an_adapter.md#defining-an-adapter-instance)
    * [Adding a Configuration Field to an Adapter Instance](adding_to_an_adapter.md#adding-a-configuration-field-to-an-adapter-instance)
    * [Adding a Credential](adding_to_an_adapter.md#adding-a-credential)
    * [Creating an Adapter Instance](adding_to_an_adapter.md#creating-an-adapter-instance)
    * [Adding an Object Type](adding_to_an_adapter.md#adding-an-object-type)
    * [Creating an Object](adding_to_an_adapter.md#creating-an-object)
    * [Adding an Attribute](adding_to_an_adapter.md#adding-an-attribute)
    * [Creating a Metric or Property](adding_to_an_adapter.md#creating-a-metric-or-property)
    * [Creating an Event](adding_to_an_adapter.md#creating-an-event)
    * [Creating a Relationship](adding_to_an_adapter.md#creating-a-relationship)
* [Adding Content](adding_content.md)
    * [Adding a Dashboard](adding_content.md#adding-a-dashboard)
    * [Adding a Report Template](adding_content.md#adding-a-report-template)
    * [Adding Alert Definitions](adding_content.md#adding-alert-definitions)
    * [Adding a Traversal](adding_content.md#adding-a-traversal)
    * [Adding Localization](adding_content.md#adding-localization)


### Extending an Existing Management Pack

This guide assumes you have already set up the SDK and know how to create a new project.
It walks you through the steps necessary to extend an existing Management Pack to add
additional data, using the MySQL Management Pack as an example.

Extending an existing management pack is similar to creating a new management pack, but
has some additional constraints. This section will create a management pack that adds
metrics to the existing MySQL management pack's database object. It assumes
you have already installed the SDK and understand the tools and steps in the 'Get
Started' section. It also assumes that you have installed and configured the [MySQL
management pack](https://customerconnect.vmware.com/downloads/details?downloadGroup=VRTVS_MP_MYSQL_810&productId=1051)
on a VMware Aria Operations instance in your local network.

For the purposes of this walkthrough, we will be adding five metrics to the MySQL database
object that show the total amount of lock waits and statistics about the time spent
waiting for those locks. This info can be found in MySQL in the table
`performance_schema.table_lock_waits_summary_by_table`.

The first step is to run `mp-init` and create a new project. There are no restrictions,
except that the adapter kind key cannot be used by another management pack that is
installed on the same system. For example, we used the following to create the sample:

```
❯ mp-init
Enter a directory to create the project in. This is the directory where adapter code, metadata, and
content will reside. If the directory doesn't already exist, it will be created.
Path: mysql-extension-mp
Management pack display name: Extended MySQL MP
Management pack adapter key: ExtendedMySQLMP
Management pack description: Adds 'Lock Wait' metrics to MySQL Database objects
Management pack vendor: VMware, Inc
Enter a path to a EULA text file, or leave blank for no EULA:
Enter a path to the management pack icon file, or leave blank for no icon:
An icon can be added later by setting the 'pak_icon' key in 'manifest.txt' to the
icon file name and adding the icon file to the root project directory.
Creating Project [Finished]

project generation completed
```

The completed management pack is found in
[the 'samples' directory](samples/mysql-extension-mp), and can be used as a reference
for this walkthrough or as a starting point for creating your own.

Once the project finished generating, we can change directory into the project
and activate the Python virtual environment.

Next, we need to modify the adapter code. We will break this up into several steps:
1. [Add a library for connecting to MySQL](#add-a-library-for-connection-to-mysql)
2. [Modify the adapter definition to add fields for connecting to MySQL](#modify-the-adapter-definition-to-add-fields-for-connecting-to-mysql)
3. [Modify the `test` method to create a MySQL connection and run a query](#modify-the-test-method-to-create-a-mysql-connection-and-run-a-query)
4. [Modify the `collect` method to collect metrics, and attach them to the correct
   database objects](#modify-the-collect-method-to-collect-metrics-and-attach-them-to-the-correct-database-objects)
5. [Verify the MP](#verify-the-mp)

#### Add a library for connection to MySQL

In order to add the metrics we want, we will need to be able to run a query against a
MySQL database. There are several Python libraries that can help us do this. For now,
let's use [`mysql-connector-python`](https://dev.mysql.com/doc/connector-python/en/).

To add a library to the adapter, open the file `adapter_requirements.txt` and add a new
line with the name of the library. Optionally, we can also add a version constraint.
Here's what the modified file should look like:
```
vmware-aria-operations-integration-sdk-lib==0.7.*
psutil
mysql-connector-python>=8.0.32
```

> Note: We can also remove the `psutil` library, as that is only used in the sample code
> that we will be replacing. However, we would then no longer be able to run `mp-test`
> until we have removed the sample code that depends on `psutil`, so for now we will
> keep it.

#### Modify the adapter definition to add fields for connecting to MySQL

Now that we have added the library, we need to see what information it needs in order
to connect. Since the adapter will be running on the VMware Aria Operations Cloud Proxy,
which is not where our MySQL instance is running, we will need the following:
* Host
* Port
* Username
* Password

In the `app/adapter.py` file, find the `get_adapter_definition()` method. We will define
parameters for the `Host` and `Port`, and a credential for the `Username` and `Password`.
After also removing the 'ID' parameter from the sample adapter, the method should look
similar to this:

```python
def get_adapter_definition() -> AdapterDefinition:
    logger.info("Starting 'Get Adapter Definition'")
    definition = AdapterDefinition(ADAPTER_KIND, ADAPTER_NAME)

    definition.define_string_parameter("host", "MySQL Host")
    definition.define_int_parameter("port", "Port", default=3306)

    credential = definition.define_credential_type("mysql_user", "MySQL User")
    credential.define_string_parameter("username", "Username")
    credential.define_password_parameter("password", "Password")

    # The key 'container_memory_limit' is a special key that is read by the VMware Aria
    # Operations collector to determine how much memory to allocate to the docker
    # container running this adapter. It does not need to be read inside the adapter
    # code.
    definition.define_int_parameter(
        "container_memory_limit",
        label="Adapter Memory Limit (MB)",
        description="Sets the maximum amount of memory VMware Aria Operations can "
                    "allocate to the container running this adapter instance.",
        required=True,
        advanced=True,
        default=1024,
    )

    # This Adapter has no object types directly, rather it co-opts object types that
    # are part of the MySQL MP to add additional metrics. As such, we can't define
    # those object types here, because they're already defined in the MySQL MP with a
    # different adapter type.

    # If we decide to also create new objects (that are not part of an existing MP),
    # those can be added here.

    logger.info("Finished 'Get Adapter Definition'")
    logger.debug(f"Returning adapter definition: {definition.to_json()}")
    return definition
```

The adapter definition is also where objects and metrics are defined, however we are
only allowed to define objects and metrics that are a part of our adapter type. Because
extensions modify objects that are part of a different adapter type, we can't add them.
This means that we can't set metric metadata like 'units', 'labels', etc that we would
generally be able to set.

#### Modify the `test` method to create a MySQL connection and run a query

Now that we've defined our parameters, we can try to connect and run a test query.
We will do this in the `test` method. Notice this takes an `AdapterInstance` as a
parameter. We will replace all the code that is inside the try/except block.

All the parameters and credentials from the definition will be present in this Adapter
Instance. We can access them like this, using the `key`s that we defined in the
`get_adapter_definition` function to get the value assigned to that parameter:

```python
    hostname = adapter_instance.get_identifier_value("host")
    port = int(adapter_instance.get_identifier_value("port", "3306"))
    username = adapter_instance.get_credential_value("username")
    password = adapter_instance.get_credential_value("password")
```

We can then use them to connect to MySQL and run a test query (be sure to import
`mysql.connector`):

```python

    connection = mysql.connector.connect(
        host=hostname,
        port=port,
        user=username,
        password=password,
    )
    cursor = connection.cursor()

    # Run a simple test query
    cursor.execute("SHOW databases")
    for database in cursor: # The cursor needs to be consumed before it is closed
        logger.info(f"Found database '{database}'")
    cursor.close()
```

Since we can expect that this will fail, e.g., if the user provides the wrong username
and password, we should ensure there is good error-handling in this function.

If we detect a failure (e.g., in the `except` block), we should call
`result.with_error(error_message)` to indicate the test has failed. If no errors have
been attached to the `result` object, the test will pass. (Note that calling
`result.with_error(...)` multiple times in the same test will result in only the last
error being displayed.)

If the management pack will be widely distributed, it may also be worthwhile to catch
common errors and ensure the resulting messages are clear and user-friendly.

We should now be able to run `mp-test connect` to run this code. The `mp-test` tool
will ask you to create a new connection, prompting for 'host', 'port', 'username', and
'password'. After, it will ask if it should override SuiteAPI<sup>1</sup> credentials. Unless you
have already set these up, select 'Yes', as we will need them later when we modify the
'collect' method. It will ask you for the SuiteAPI hostname, which should be the
hostname of the VMware Aria Operations instance where the MySQL management pack is
running, and a username and password which have permission to access to the SuiteAPI on
that system.

> <sup>1</sup>SuiteAPI is a REST API on VMware Aria Operations that can be used for many
> purposes. The documentation for this API can be found on any VMware Aria Operations
> instance at https://[aria_ops_hostname]/suite-api/. The 'adapter_instance' object that
> is passed to the 'test', 'get_endpoints', and 'collect' methods can automatically
> connect to this API and has methods for querying it.

If everything was successful, the result should look similar to this:
```
(venv-Extended MySQL MP) ❯ mp-test connect
Choose a connection:  New Connection
Building adapter [Finished]
Waiting for adapter to start [Finished]
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│Connections are akin to Adapter Instances in VMware Aria Operations, and contain the parameters                                             │
│needed to connect to a target environment. As such, the following connection parameters and credential fields are                           │
│derived from the 'conf/describe.xml' file and are specific to each Management Pack.                                                         │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
Enter connection parameter 'MySQL Host': mysql8-1.localnet
Enter connection parameter 'Port': 3306
Enter connection parameter 'Adapter Memory Limit (MB)': 1024
Enter credential field 'Username': root
Enter credential field 'Password': *********
Override default SuiteAPI connection information for SuiteAPI calls?  Yes
Suite API Hostname: aria-ops-1.vmware.com
Suite API User Name: admin
Suite API Password: ********
Set these as the default SuiteAPI connection?  Yes
Enter a name for this connection: default
Saved connection 'default' in '~/Code/extended-mysql-mp/config.json'.
The connection can be modified by manually editing this file.
Building adapter [Finished]
Waiting for adapter to start [Finished]
Running Endpoint URLs [Finished]
Running Connect [Finished]
{}

Avg CPU %                     | Avg Memory Usage %         | Memory Limit | Network I/O         | Block I/O
------------------------------+----------------------------+--------------+---------------------+--------------
14.9 % (0.0% / 14.9% / 29.8%) | 4.0 % (4.0% / 4.0% / 4.0%) | 1.0 GiB      | 9.06 KiB / 4.16 KiB | 0.0 B / 0.0 B

Request completed in 1.85 seconds.

All validation logs written to '~/Code/mysql-extention-mp/logs/validation.log'
Validation passed with no errors
```

#### Modify the `collect` method to collect metrics, and attach them to the correct database objects

Now that the `test` method is working, we can implement the `collect` method. This is
the method where we query MySQL for the metrics we want and send them to VMware Aria
Operations as part of the database objects. Before we begin writing code, we need to
look up some information about the MySQL management pack. Specifically, we need the
following information:
* The MySQL Adapter Kind Key
* The MySQL Database Object type
* A way to create a database object that matches a database that already exists on
  VMware Aria Operations (usually the identifier list, but the name can sometimes work,
  as in this case).

These will be used to ensure that the metrics are attached to existing MySQL objects,
rather than creating new ones.

To get this information, we will `ssh` into the collector where the MySQL management
pack is running. Then `cd` to `$ALIVE_BASE/user/plugin/inbound/mysql_adapter3/conf/`.
From there, open the `describe.xml` file. The Adapter Kind key is at the top on the
fourth line:
```xml
<?xml version = '1.0' encoding = 'UTF-8'?>
<!-- <!DOCTYPE AdapterKind SYSTEM "describeSchema.xsd"> -->
<!-- Copyright (c) 2020 VMware Inc. All Rights Reserved. -->
<AdapterKind key="MySQLAdapter" nameKey="1" version="1" xmlns="http://schemas.vmware.com/vcops/schema">
```
Inside the `AdapterKind` tag are `ResourceKinds/ResourceKind` tags, and we can search
for the one that represents the database resource kind. Once we have found it we can see
that it has two identifiers, one for the adapter instance ID, and one for the database
name.
```xml
   <ResourceKinds>
      <!-- ... -->
      <ResourceKind key="mysql_database" nameKey="64" >
          <ResourceIdentifier dispOrder="1" key="adapter_instance_id" length="" nameKey="37" required="true" type="string" identType="1" enum="false" default=""> </ResourceIdentifier>
          <ResourceIdentifier dispOrder="2" key="database_name" length="" nameKey="65" required="true" type="string" identType="1" enum="false" default=""> </ResourceIdentifier>
```
In order to attach a metric to these objects, we will need all identifiers that have an
`identType=1`. In this case, those are `adapter_instance_id` and `database_name`. This
means that the combination of those two fields uniquely identify the object among all
of the `mysql_database` objects in the `MySQLAdapter` adapter.

Getting the `adapter_instance_id` requires a SuiteAPI call. We need to retrieve the
Adapter Instances for `MySQLAdapter` that has the same host and port identifiers as our
adapter, and then retrieving the id. However, if we look in VMware Aria Operations
itself, we can see that each database's name has the format `mysql_host/mysql_database`,
which should be unique (even if VMware Aria Operations isn't using it for determining
uniqueness). Thus, a simpler way to get matching objects (in this case) is to construct
the name, and ask the SuiteAPI to give us all `MySQLAdapter` `mysql_database` objects
with those names. Then we can simply attach metrics to the resulting `mysql_database`
objects, which will have all identifiers correctly set by the SuiteAPI.

First, we should remove all the sample code inside the `try` block. All the code for the
following steps should be inside the `try` block.

Then, we need to establish a connection to MySQL. We can do this in the same way as in
test connect. In many cases creating a function for connecting that is called from both
`test` and `collect` is worthwhile. Then we can query the list of databases, and
construct a list of database names that may be present:

```python
        # Get the list of databases on this instance
        cursor = connection.cursor()
        cursor.execute("SHOW databases")
        database_names = [f"{hostname}/{database[0]}" for database in cursor]
        cursor.close()
```

We then query the SuiteAPI for `mysql_database` objects from the `MySQLAdapter`
adapter, with the names we computed. The queries that `query_for_resources` accepts
are documented in the SuiteAPI documentation, and can search on many types of metadata
about a resource. After that, we add the returned objects to the `result` and to a
dictionary for quick access later.

```python
        # Get the list of objects from the SuiteAPI that represent the MySQL
        # databases that are on this instance, and add any we find to the result
        databases = {}  # dict of database Objects by name for easy access
        with adapter_instance.suite_api_client as suite_api:
            dbs = suite_api.query_for_resources(
                query={
                    "adapterKind": ["MySQLAdapter"],
                    "resourceKind": ["mysql_database"],
                    "name": database_names,
                },
            )
            for db in dbs:
                databases[db.get_identifier_value("database_name")] = db
                # Add each database to the collection result. Objects must be
                # added to the result in order for them to be returned by the
                # collect method.
                result.add_object(db)
```

Finally, we'll run the query to get the data from MySQL that we want, and add that data
as metrics to the relevant databases, and return the result:

```python
        # Run a query to get some additional data. Here we're getting info about
        # lock waits on each database
        cursor = connection.cursor()
        cursor.execute("""
                    select OBJECT_SCHEMA,
                           sum(COUNT_STAR)     as COUNT_STAR,
                           sum(SUM_TIMER_WAIT) as SUM_TIMER_WAIT,
                           max(MAX_TIMER_WAIT) as MAX_TIMER_WAIT,
                           min(MIN_TIMER_WAIT) as MIN_TIMER_WAIT
                    from performance_schema.table_lock_waits_summary_by_table
                    group by OBJECT_SCHEMA
                    """)

        # Iterate through the results of the query, and add them to the appropriate
        # database Object as metrics.
        for row in cursor:
            if len(row) != 5:
                logger.error(f"Row is not expected size: {repr(row)}")
                continue
            database = databases.get(row[0])
            if not database:
                logger.info(f"Database {row[0]} not found in Aria Operations")
                continue
            database.with_metric("Table Locks|Count", float(row[1]))
            database.with_metric("Table Locks|Sum", float(row[2]))
            database.with_metric("Table Locks|Max", float(row[3]))
            if float(row[1] > 0):
                database.with_metric("Table Locks|Avg", float(row[2])/float(row[1]))
            else:
                database.with_metric("Table Locks|Avg", 0)
            database.with_metric("Table Locks|Min", float(row[4]))
        cursor.close()

        return result
```

#### Verify the MP

To verify the MP, run `mp-test` using the same connection we created earlier. If there
are any `mysql_database` objects that have entries in the
`table_lock_waits_summary_by_table` table, we should see those returned in the
collection result. For example, if the MySQL management pack is configured to collect
`loadgen`, `mysql`, and `sys`, and the data query returns:
```
object_schema      | count_star | sum_timer_wait | max_timer_wait | min_timer_wait
-------------------+------------+----------------+----------------+---------------
mysql              | 0          | 0              |0               | 0
performance_schema | 0          | 0              |0               | 0
sys                | 2          | 3946368        |2255204         | 1691164
```
Then we would expect to see entries for each database monitored by MySQL, but new
data should be present only for the subset that was also returned by the data query:
```json
{
    "nonExistingObjects": [],
    "relationships": [],
    "result": [
        {
            "events": [],
            "key": {
                "adapterKind": "MySQLAdapter",
                "identifiers": [
                    {
                        "isPartOfUniqueness": true,
                        "key": "adapter_instance_id",
                        "value": "347062"
                    },
                    {
                        "isPartOfUniqueness": true,
                        "key": "database_name",
                        "value": "loadgen"
                    }
                ],
                "name": "mysql8-1.localnet/loadgen",
                "objectKind": "mysql_database"
            },
            "metrics": [],
            "properties": []
        },
        {
            "events": [],
            "key": {
                "adapterKind": "MySQLAdapter",
                "identifiers": [
                    {
                        "isPartOfUniqueness": true,
                        "key": "adapter_instance_id",
                        "value": "347062"
                    },
                    {
                        "isPartOfUniqueness": true,
                        "key": "database_name",
                        "value": "mysql"
                    }
                ],
                "name": "mysql8-1.localnet/mysql",
                "objectKind": "mysql_database"
            },
            "metrics": [
                {
                    "key": "Table Locks|Count",
                    "numberValue": 0.0,
                    "timestamp": 1681767040181
                },
                {
                    "key": "Table Locks|Sum",
                    "numberValue": 0.0,
                    "timestamp": 1681767040181
                },
                {
                    "key": "Table Locks|Max",
                    "numberValue": 0.0,
                    "timestamp": 1681767040181
                },
                {
                    "key": "Table Locks|Avg",
                    "numberValue": 0.0,
                    "timestamp": 1681767040181
                },
                {
                    "key": "Table Locks|Min",
                    "numberValue": 0.0,
                    "timestamp": 1681767040181
                }
            ],
            "properties": []
        },
        {
            "events": [],
            "key": {
                "adapterKind": "MySQLAdapter",
                "identifiers": [
                    {
                        "isPartOfUniqueness": true,
                        "key": "adapter_instance_id",
                        "value": "347062"
                    },
                    {
                        "isPartOfUniqueness": true,
                        "key": "database_name",
                        "value": "sys"
                    }
                ],
                "name": "mysql8-1.localnet/sys",
                "objectKind": "mysql_database"
            },
            "metrics": [
                {
                    "key": "Table Locks|Count",
                    "numberValue": 2.0,
                    "timestamp": 1681767040182
                },
                {
                    "key": "Table Locks|Sum",
                    "numberValue": 3946368.0,
                    "timestamp": 1681767040182
                },
                {
                    "key": "Table Locks|Max",
                    "numberValue": 2255204.0,
                    "timestamp": 1681767040182
                },
                {
                    "key": "Table Locks|Avg",
                    "numberValue": 1973184.0,
                    "timestamp": 1681767040182
                },
                {
                    "key": "Table Locks|Min",
                    "numberValue": 1691164.0,
                    "timestamp": 1681767040182
                }
            ],
            "properties": []
        }
    ]
}
```

When everything is working as expected locally using `mp-test`, we can run
`mp-build` and install on VMware Aria Operations for a final verification.


#### Next Steps

* [Adding to an Adapter](adding_to_an_adapter.md)
    * [Defining an Adapter](adding_to_an_adapter.md#defining-an-adapter)
    * [Defining an Adapter Instance](adding_to_an_adapter.md#defining-an-adapter-instance)
    * [Adding a Configuration Field to an Adapter Instance](adding_to_an_adapter.md#adding-a-configuration-field-to-an-adapter-instance)
    * [Adding a Credential](adding_to_an_adapter.md#adding-a-credential)
    * [Creating an Adapter Instance](adding_to_an_adapter.md#creating-an-adapter-instance)
    * [Adding an Object Type](adding_to_an_adapter.md#adding-an-object-type)
    * [Creating an Object](adding_to_an_adapter.md#creating-an-object)
    * [Adding an Attribute](adding_to_an_adapter.md#adding-an-attribute)
    * [Creating a Metric or Property](adding_to_an_adapter.md#creating-a-metric-or-property)
    * [Creating an Event](adding_to_an_adapter.md#creating-an-event)
    * [Creating a Relationship](adding_to_an_adapter.md#creating-a-relationship)
* [Adding Content](adding_content.md)
    * [Adding a Dashboard](adding_content.md#adding-a-dashboard)
    * [Adding a Report Template](adding_content.md#adding-a-report-template)
    * [Adding Alert Definitions](adding_content.md#adding-alert-definitions)
    * [Adding a Traversal](adding_content.md#adding-a-traversal)
    * [Adding Localization](adding_content.md#adding-localization)
