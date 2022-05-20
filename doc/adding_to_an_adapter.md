Adding to an Adapter
====================
## Creating an adapter instance
An adapter instance is a special object in vROps that stores user configuration for a connection. Every adapter should have exactly one adapter instance. Adapter instances are set by defining a `ResourceKind` element with attribute `type=7`.
```xml
  <ResourceKinds>
    <ResourceKind key="my_adapter_instance" nameKey="4" type="7" >
        <...>
    </ResourceKind>
  </ResourceKinds>
```

Once an adapter instance is defined, any configuration fields (`ResourceIdentifiers`) will be prompted to the user when creating an account on the Data Sources -> Integrations page.
After the account has been created, configuration fields will be available in the input to the `collect`, `test_connection`, and `get_endpoint_urls` methods.

## Adding a configuration field to an Adapter Instance

Adapter instance _identifiers_ distinguish between adapter instances from the same adapter. They also allow for user configuration.

```xml
  <ResourceKinds>
    <ResourceKind key="my_adapter_instance" nameKey="4" type="7" >
        <ResourceIdentifier dispOrder="1" key="instance" nameKey="5" required="true" type="string" identType="1"/>
        <ResourceIdentifier dispOrder="2" key="ssl_mode" nameKey="6" required="true" type="string" identType="2" enum="true">
            <enum default="true" value="Disable" />
            <enum default="false" value="Require" />
        </ResourceIdentifier>
        <ResourceIdentifier dispOrder="3" key="max_events" nameKey="7" required="false" type="integer" identType="2"/>
    </ResourceKind>
</ResourceKinds>
```
For more information about the supported elements and attributes, see the [describe.xml documentation](describeSchema.xsd).

Adapter instance identifiers can have an `identType` of `1` or `2`. A type of `1` means the identifier will be used for determining uniqueness, and will show up by default on the configuration page. If the type is `2`, the identifier is _non-identifying_, and will show up under the 'advanced' section of the configuration page.

Using the [Python vROps Integration Module](python-integration-module.md), the canonical method for reading the configuration is using the `AdapterInstance` object.

```python
adapter_instance = AdapterInstance.from_input(sys.argv[-2]) # The input file is always the second to last argument
instance = adapter_instance.get_identifier_value("instance")
ssl_mode = adapter_instance.get_identifier_value("ssl_mode")
max_events = adapter_instance.get_identifier_value("max_events")
```

For other languages, or using Python without the vROps Integration module, objects must be returned as json, described in the [vROps Collector Framework OpenAPI Document](../api/vrops-collector-fwk2-openapi.json).


## Adding a credential

In order to connect to most targets a credential is required. If necessary, an adapter can have multiple different credential kinds.
To add a credential to the Adapter, add a `CredentialKind` element to `AdapterKind/CredentialKinds` in the `conf/describe.xml` file. The `CredentialKind` element takes one or more `CredentialField` elements which correspond to an individual piece of data needed for a credential. A typical credential that requires a username and password might look like this:
```xml
  <CredentialKinds>
    <CredentialKind key="my_credential_type" nameKey="1" >
      <CredentialField required="true" dispOrder="0" enum="false" key="username" nameKey="2" password="false" type="string">
      </CredentialField>
      <CredentialField required="false" dispOrder="1" enum="false" key="password" nameKey="3" password="true" type="string">
      </CredentialField>
    </CredentialKind>
  </CredentialKinds>
```
For more information about the supported elements and attributes, see the [describe.xml documentation](describeSchema.xsd).
Once the credential is defined, it must be added to the Adapter Instance. The adapter instance is a special `ResourceKind` that is used to configure an adapter. It is marked with the xml attribute/value `type="7"`. To add the credential to the adapter instance, add an attribute `credentialKind` to the adapter instance's `ResourceKind` element, with a value of the `CredentialKind`'s `key` attribute. In the case where multiple credential kinds are supported, the keys are separated by a comma.
```xml
  <ResourceKinds>
    <ResourceKind key="my_adapter_instance" credentialKind="my_credential_type" nameKey="4" type="7" >
        <...>
    </ResourceKind>
  </ResourceKinds>
```

Once the credential is defined in the `describe.xml` file, it can be used in the adapter code.
Using the [Python vROps Integration Module](python-integration-module.md), the credential is accessed from the `AdapterInstance` object's `credentials` property.
For other languages, or using Python without the vROps Integration module, the credential is accessed from the input json using the path `credential_config.credential_fields`
> Note: If there are any existing connections used by the [`mp-test`](mp-test.md) tool before the credential was created or updated, these will need to be deleted or updated.

## Adding an object type

An object type is a class of objects (resources) that share the same set of metrics, properties, and identifiers. For example an adapter might have a 'Database' object kind, and when an adapter instance is created and connects to an application, several 'database' objects are created representing distinct databases in the application. To create a new object type, add a `ResourceKind` element inside `AdapterKind/ResourceKinds` in the `conf/describe.xml` file.
A `key` attribute is required, and must be unique among other object types within the `describe.xml` file. 

In addition, an object type may have _identifiers_, which can distinguish between objects of the same type. In the database example, we may need to know a `port` and `ip address` to uniquely identify each database. If no identifiers are specified, an object's `name` is used for determining uniqueness. If any identifiers are present (see note), then the `name` is not used for this purpose.
```xml
  <ResourceKinds>
    <...>
    <ResourceKind key="my_database_resource_kind" nameKey="8">
        <ResourceIdentifier dispOrder="1" key="server_ip" nameKey="9" required="true" type="string" identType="1"/>
        <ResourceIdentifier dispOrder="2" key="server_port" nameKey="10" required="true" type="integer" identType="1"/>
        <...>
    </ResourceKind>
</ResourceKinds>
```
For more information about the supported elements and attributes, see the [describe.xml documentation](describeSchema.xsd).

> Note: Identifiers can have an `identType` of `1` or `2`. A type of `1` is most common, and means the identifier will be used for determining uniqueness. If the type is `2`, the identifier is _non-identifying_, and will show up in the identifiers of an object but will not cause a new object to be created if it changes. If _all_ identifiers are non-identifying, then the object's name reverts to determining uniqueness of objects. 

Once the object type is defined in the `describe.xml` file, it can be used in the adapter code.

Using the [Python vROps Integration Module](python-integration-module.md), the canonical method for creating a new object is to use the `CollectResult` object.

```python
import sys

result = CollectResult()
database1 = result.object(adapter_kind="my_adapter_kind", object_kind="my_database_resource_kind", name="db1",
                          identifiers=[
                              Identifier("server_ip", "10.0.34.1"),
                              Identifier("server_port", 110)
                          ])
# <additional collection code>
# ...

# send database1 (and any other objects in the CollectResult) back to vROps
result.send_result(sys.argv[-1]) # The output file is always the second to last argument
```

For other languages, or using Python without the vROps Integration module, objects must be returned as json, described in the [vROps Collector Framework OpenAPI Document](../api/vrops-collector-fwk2-openapi.json).

## Adding an attribute (metrics and properties)
An attribute is a class of metric or property similar to how an object type is a class of objects. Attributes can be either a metric or property.
* A metric is numeric data that is useful to track over time. Example: CPU Utilization (%)
* A property is (generally) string data that rarely changes and only the current (last) value is relevant. Example: CPU Count

> Note: Properties should not be used for string data that has a large number of possible values, such as timestamps. For example, if you want to have a property that shows the last boot time of a server, it is better to convert that to a numeric metric such as `days_since_last_boot`. A large number of distinct string values can degrade the performance of vROps.

Attributes can be grouped together in `ResourceGroup` elements, which can be nested. `ResourceGroups` can also be instanced.
```xml
    <ResourceKind key="my_database_resource_kind" nameKey="8">
        <ResourceIdentifier dispOrder="1" key="server_ip" nameKey="9" required="true" type="string" identType="1"/>
        <ResourceIdentifier dispOrder="2" key="server_port" nameKey="10" required="true" type="integer" identType="1"/>
        <ResourceGroup nameKey="4" key="tablespace">
            <ResourceAttribute nameKey="11" dashboardOrder="1" key="tablespace_name" dataType="string" isProperty="true" />
            <ResourceAttribute nameKey="12" dashboardOrder="2" key="reads" dataType="integer" isProperty="false" />
        </ResourceGroup>
        <ResourceAttribute nameKey="12" dashboardOrder="1" key="session_count" dataType="integer" isProperty="false" />
    </ResourceKind>
```
For more information about the supported elements and attributes, see the [describe.xml documentation](describeSchema.xsd).

Once an attribute is defined in the `describe.xml` file, it can be used in the adapter code.

Using the [Python vROps Integration Module](python-integration-module.md), metrics and properties can be added using the attribute key and a value. In the case of attributes in groups, the group(s) and attribute key are separated by a pipe "|" and form the metric or property key.
```python
database1 = # Object
database1.with_property("tablespace|tablespace_name", "MyTablespace")
database1.with_metric("tablespace|reads", 104)
database1.with_metric("session_count", 5)
```

For other languages, or using Python without the vROps Integration module, metrics and properties are returned as json inside of objects, described in the [vROps Collector Framework OpenAPI Document](../api/vrops-collector-fwk2-openapi.json).

## Adding an event
Events do not need to be declared in the `describe.xml` file, and can simply be added to an object at runtime.

Using the [Python vROps Integration Module](python-integration-module.md), events are added to resources. The only required parameter is the message, which describes and uniquely identifies the event.
```python
database1 = # Object
database1.with_event(
    message="Database read latency is above threshold", criticality=Criticality.IMMEDIATE)
```

For other languages, or using Python without the vROps Integration module, events are returned as json inside of objects, described in the [vROps Collector Framework OpenAPI Document](../api/vrops-collector-fwk2-openapi.json).
## Adding a relationship
Relationships do not need to be declared in the `describe.xml` file, and can simply be added between objects at runtime. Relationships are always between a _parent_ and _child_, and if object1 is a parent of object2, that implies object2 is a child of object1.

Using the [Python vROps Integration Module](python-integration-module.md), relationships are added to resources.
```python
instance = # Object
database1 = # Object
database2 = # Object
instance.add_child(database1)
database2.add_parent(instance) 
# database2 and database1 both have the same relationship with respect to the instance object after these calls
```
For other languages, or using Python without the vROps Integration module, relationships are returned as json inside of a collect result object, described in the [vROps Collector Framework OpenAPI Document](../api/vrops-collector-fwk2-openapi.json).
