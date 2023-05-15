# Describe XML

This XML configuration file defines the object model for an adapter, along with semantic definitions for use in data 
analysis and management. This file must be included in the Management Pack. By default, the `adapter.py` file comes with a 
**get_adapter_definition()** method that returns an [AdapterDefinition](../lib/python/doc/src/aria/ops/definition/adapter_definition.html).
The SDK tools use the `AdapterDefinition` returned by this method to generate a describe.xml file that conforms to the 
required schema. However, users can also write the describe.xml file  manually adding one to the `content` folder. If a 
describe.xml file is in the content folder, the SDK tools will avoid generating one. `mp-test collect` validates the describe.xml
file against the collection result and outputs the validation result to a `log/validation.log` file. There should not be
errors in the describe.xml file; otherwise, the management Pack installation might fail. 

## Defining an Adapter Object Model:

In the following documentation we break the different Elements of the describe.xml and show how they are defined using
[aria-operations-integration-sdk-lib](https://pypi.org/project/vmware-aria-operations-integration-sdk-lib) Python module.  

### Adapter 
When defining an adapter model in the describe.xml file, we first have to define the `<AdapterKind>` element along with 
a `<ResourceKind>` element. The `<AdapterKind>` element is the root element of a describe.xml file, and it contains the 
model for the monitored resources. Along with a root `<AdapterKind>`element, every describe.xml requires
at least one `<ResourceKind>` element for the adapter instance. This object type represents the adapter itself when it 
is instantiated in a VMware Aria Operations node. The [AdapterDefinition](../lib/python/doc/src/aria/ops/definition/adapter_definition.html), 
defines the `<AdapterKind>` and the `<ResourceKind>` by using the key passed to its constructor. 

Python 
```python
def get_adapter_definition() -> AdapterDefinition:
    definition = AdapterDefinition("MyAdapter", "My Adapter")
```
describe.xml 
```xml
<AdapterKind key="MyAdapter" nameKey="My Adapter" version="1" >
    <CredentialKinds/>
    <ResourceKinds>
        <ResourceKind key="MyAdapter_adapter_instance" nameKey="2" type="7" credentialKind=""/>
    </ResourceKinds>
</AdapterKind>
```

### Credentials and Input Parameters
After defining our root element and base the adapter resource we can define any credentials and parameters needed by our 
adapter during configuration. To implement a credential feature, we must include a `<CredentialKinds>` section element 
in describe.xml along with each `<CredentialField>`. in the Python SDK we can use the `define_credential_type` function 
which defines a new credential type and adds it to the `AdapterDefinition` object; then we can specify each credential 
field using the returned [CredentialType](../lib/python/doc/src/aria/ops/definition/credential_type.html). An adapter 
stores the credential in encrypted form and uses it to establish a secure connection to an information source.

Python
```python
def get_adapter_definition() -> AdapterDefinition:
    definition = AdapterDefinition("MyAdapter", "My Adapter")
    
+    credential = definition.define_credential_type"vsphere_user", "Credential")
+    credential.define_string_parameter("user_name", "User Name")
+    credential.define_password_parameter("user_password", "Password")
```
describe.xml
```xml
<AdapterKind key="MyAdapter" nameKey="1" version="1">
+    <CredentialKinds>
+        <CredentialKind key="vsphere_user" nameKey="2">
+            <CredentialField key="user" nameKey="3" required="true" dispOrder="0" password="false" enum="false" type="string"/>
+            <CredentialField key="password" nameKey="4" required="true" dispOrder="1" password="true" enum="false" type="string"/>
+        </CredentialKind>
+    </CredentialKinds>
    <ResourceKinds>
+        <ResourceKind key="MyAdapter_adapter_instance" nameKey="2" type="7" credentialKind="vsphere_user"/>
    </ResourceKinds>
</AdapterKind>
```

To define parameter we can add `<ResourceIdentifier>` elements to the adapter `<ResourceKind>` element. In the Python SDK, 
we can use one of the `define_string_parameter`,`define_enum_parameter`, or `define_int_parameter` functions according to
the type of parameter we want would like to define.

Python
```python
def get_adapter_definition() -> AdapterDefinition:
    definition = AdapterDefinition("MyAdapter", "My Adapter")

    credential = definition.define_credential_type"vsphere_user", "Credential")
    credential.define_string_parameter("user_name", "User Name")
    credential.define_password_parameter("user_password", "Password")
    
+    definition.define_string_parameter(
+    "ID",
+    label="ID",
+    description="Example identifier. Using a value of 'bad' will cause "
+    "test connection to fail; any other value will pass.",
+    required=True,
+    )

+    definition.define_int_parameter(
+    "container_memory_limit",
+    label="Adapter Memory Limit (MB)",
+    description="Sets the maximum amount of memory VMware Aria Operations can "
+    "allocate to the container running this adapter instance.",
+    required=True,
+    advanced=True,
+    default=1024,
+    )
```

describe.xml
```xml
<AdapterKind key="MyAdapter" nameKey="1" version="1">
    <CredentialKinds>
        <CredentialKind key="vsphere_user" nameKey="2">
            <CredentialField key="user" nameKey="3" required="true" dispOrder="0" password="false" enum="false" type="string"/>
            <CredentialField key="password" nameKey="4" required="true" dispOrder="1" password="true" enum="false" type="string"/>
        </CredentialKind>
    </CredentialKinds>
    <ResourceKinds>
        <ResourceKind key="MyAdapter_adapter_instance" nameKey="2" type="7" credentialKind="vsphere_user">
+            <ResourceIdentifier default="" key="ID" nameKey="3" required="true" dispOrder="0" enum="false" type="string" identType="1"/>
+            <ResourceIdentifier default="1024" key="container_memory_limit" nameKey="4" required="true" dispOrder="1" enum="false" type="integer" identType="2"/>
        </ResourceKind>
    </ResourceKinds>
</AdapterKind>
```

### Resources
In addition `<ResourceKind>` that represent the running instance of our adapter, the `<ResourceKind>` element is used to
define each resource that your adapter will collect at runtime. In the Python SDK we can simply use the `define_object_type`
function.

Python
```python
def get_adapter_definition() -> AdapterDefinition:
    definition = AdapterDefinition("MyAdapter", "My Adapter")

    credential = definition.define_credential_type"vsphere_user", "Credential")
    credential.define_string_parameter("user_name", "User Name")
    credential.define_password_parameter("user_password", "Password")
    
    definition.define_string_parameter(
    "ID",
    label="ID",
    description="Example identifier. Using a value of 'bad' will cause "
    "test connection to fail; any other value will pass.",
    required=True,
    )

    definition.define_int_parameter(
    "container_memory_limit",
    label="Adapter Memory Limit (MB)",
    description="Sets the maximum amount of memory VMware Aria Operations can "
    "allocate to the container running this adapter instance.",
    required=True,
    advanced=True,
    default=1024,
    )

+    definition.define_object_type("cpu", "CPU")
+    definition.define_object_type("disk", "Disk")
+    definition.define_object_type("system", "System")
```

describe.xml
```xml
<AdapterKind key="MyAdapter" nameKey="1" version="1">
    <CredentialKinds>
        <CredentialKind key="vsphere_user" nameKey="2">
            <CredentialField key="user" nameKey="3" required="true" dispOrder="0" password="false" enum="false" type="string"/>
            <CredentialField key="password" nameKey="4" required="true" dispOrder="1" password="true" enum="false" type="string"/>
        </CredentialKind>
    </CredentialKinds>
    <ResourceKinds>
        <ResourceKind key="MyAdapter_adapter_instance" nameKey="2" type="7" credentialKind="vsphere_user">
            <ResourceIdentifier default="" key="ID" nameKey="3" required="true" dispOrder="0" enum="false" type="string" identType="1"/>
            <ResourceIdentifier default="1024" key="container_memory_limit" nameKey="4" required="true" dispOrder="1" enum="false" type="integer" identType="2"/>
        </ResourceKind>
+        <ResourceKind key="cpu" nameKey="5" type="1"/>
+        <ResourceKind key="disk" nameKey="6" type="1"/>
+        <ResourceKind key="system" nameKey="7" type="1"/>
    </ResourceKinds>
</AdapterKind>
```

### Metrics and Properties

To add Metrics and properties to resources, we can use the `<ResourceAttribute>` element. `<ResourceAttribute>` has an 
`isProperty` attribute that is used to differentiate between metric and properties. Metrics are used to measure attributes 
of an object that change frequently. For example, free space on a disk. Properties, on the other hand, are used to measure 
properties of an object that don't change often. For example, the number of CPUs in a system. In the Python SDk, we can 
add properties and metric to our resources by using the `define_metric` and the `define_string_property` functions of the
[ObjectType](../lib/python/doc/src/aria/ops/definition/object_type.html) returned by the `define_object_type` function.


Python
```python
def get_adapter_definition() -> AdapterDefinition:
    definition = AdapterDefinition("MyAdapter", "My Adapter")

    credential = definition.define_credential_type"vsphere_user", "Credential")
    credential.define_string_parameter("user_name", "User Name")
    credential.define_password_parameter("user_password", "Password")
    
    definition.define_string_parameter(
    "ID",
    label="ID",
    description="Example identifier. Using a value of 'bad' will cause "
    "test connection to fail; any other value will pass.",
    required=True,
    )

    definition.define_int_parameter(
    "container_memory_limit",
    label="Adapter Memory Limit (MB)",
    description="Sets the maximum amount of memory VMware Aria Operations can "
    "allocate to the container running this adapter instance.",
    required=True,
    advanced=True,
    default=1024,
    )

+    cpu = definition.define_object_type("cpu", "CPU")
+    cpu.define_numeric_property("cpu_count", "CPU Count", is_discrete=True)
+    cpu.define_metric("user_time", "User Time", Units.TIME.SECONDS)

+    disk = definition.define_object_type("disk", "Disk")
+    disk.define_string_property("partition", "Partition")
+    disk.define_metric("free_space", "Free Space", is_discrete=True, unit=Units.DATA_SIZE.BIBYTE)

    definition.define_object_type("system", "System")
```

describe.xml
```xml
<AdapterKind key="MyAdapter" nameKey="1" version="1">
    <CredentialKinds>
        <CredentialKind key="vsphere_user" nameKey="2">
            <CredentialField key="user" nameKey="3" required="true" dispOrder="0" password="false" enum="false" type="string"/>
            <CredentialField key="password" nameKey="4" required="true" dispOrder="1" password="true" enum="false" type="string"/>
        </CredentialKind>
    </CredentialKinds>
    <ResourceKinds>
        <ResourceKind key="MyAdapter_adapter_instance" nameKey="2" type="7" credentialKind="vsphere_user">
            <ResourceIdentifier default="" key="ID" nameKey="3" required="true" dispOrder="0" enum="false" type="string" identType="1"/>
            <ResourceIdentifier default="1024" key="container_memory_limit" nameKey="4" required="true" dispOrder="1" enum="false" type="integer" identType="2"/>
        </ResourceKind>
        <ResourceKind key="cpu" nameKey="5" type="1">
+            <ResourceAttribute key="cpu_count" nameKey="6" unit="" dashboardOrder="0" dataType="integer" isProperty="true" isRate="false" isDiscrete="true" isImpact="false" defaultMonitored="true" keyAttribute="false"/>
+            <ResourceAttribute key="user_time" nameKey="7" unit="seconds" dashboardOrder="1" dataType="float" isProperty="false" isRate="false" isDiscrete="false" isImpact="false" defaultMonitored="true" keyAttribute="false"/>
        </ResourceKind>
        <ResourceKind key="disk" nameKey="6" type="1">
+            <ResourceAttribute key="partition" nameKey="12" unit="" dashboardOrder="0" dataType="string" isProperty="true" isRate="false" isDiscrete="true" isImpact="false" defaultMonitored="true" keyAttribute="false"/>
+            <ResourceAttribute key="free_space" nameKey="15" unit="bibyte" dashboardOrder="3" dataType="integer" isProperty="false" isRate="false" isDiscrete="true" isImpact="false" defaultMonitored="true" keyAttribute="false"/>
        </ResourceKind>
        <ResourceKind key="system" nameKey="7" type="1"/>
    </ResourceKinds>
</AdapterKind>
```