# Extending an Existing Management Pack
* * *

This guide assumes you have already set up the SDK and know how to create a new project.
It walks you through the steps necessary to extend an existing Management Pack to add
additional data, using the MySQL Management Pack as an example.

Extending an existing management pack is similar to creating a new management pack, but
has some additional constraints. One of the primary limitations is that attributes that
extend an existing management pack's objects cannot be defined (in code or in 
`describe.xml`), which means that they can't have any metadata set about them (e.g., 
units, labels, kpi flags, etc).

This section will create a management pack that adds
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
[the 'samples' directory](https://github.com/vmware/vmware-aria-operations-integration-sdk/tree/main/samples/mysql-extension-mp), and can be used as a reference
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

???+ note

    We can also remove the `psutil` library, as that is only used in the sample code
    that we will be replacing. However, we would then no longer be able to run `mp-test`
    until we have removed the sample code that depends on `psutil`, so for now we will
    keep it.

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
pack is running. Then `cd` to `$ALIVE_BASE/user/plugin/inbound/mysql/conf/`.
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



