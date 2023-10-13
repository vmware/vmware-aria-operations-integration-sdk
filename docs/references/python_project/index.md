# Python Project 


### Templates

All templates generate the [base project structure](../mp-init.md#base-project-structure) along with some additional 
files and directories specific to Python (highlighted below): 

``` hl_lines="3 4 10-13"
.
├── Dockerfile
├── adapter_requirements.txt
├── commands.cfg
├── config.json
├── connections.json
├── eula.txt
├── manifest.txt
├── requirements.txt
├── app
│   ├── __init__.py
│   ├── adapter.py
│   └── constants.py
├── conf
│   └── describeSchema.xsd
├── content
│   ├── alertdefs
│   │   └── alertDefinitionSchema.xsd
│   ├── customgroups
│   ├── dashboards
│   ├── files
│   │   ├── reskndmetric
│   │   ├── solutionconfig
│   │   ├── topowidget
│   │   └── txtwidget
│   ├── policies
│   ├── recommendations
│   ├── reports
│   ├── resources
│   ├── supermetrics
│   ├── symptomdefs
│   └── traversalspecs
│       └── traversalSpecsSchema.xsd
├── images
│   ├── AdapterKind
│   ├── ResourceKind
│   └── TraversalSpec
└── resources
    └── resources.properties
```

### app (directory)
By default, this directory contains a template adapter. The template adapter collects several objects and metrics from
the container that the adapter is running in, and can be used as a starting point for creating a new adapter. 
The template adapter uses
[vmware-aria-operations-integration-sdk-lib](https://pypi.org/project/vmware-aria-operations-integration-sdk-lib/) to
streamline the process of building adapter.
The template adapter has comments throughout the code to help new users understand the process of creating their own
adapter using the existing code. For additional guidance creating adapters see our `Guides` section.

### adapter_requirements.txt (file)
This file defines all the dependencies needed by the adapter at run time. This file is copied onto the container where
the adapter runs and used by the default Dockerfile to install dependencies into the container image.

### commands.cfg (file)
This file contains a list of the commands the HTTP server can run, along with the path to the executable related to the
command. By default, all commands are run by executing the `adapter.py` file along with a parameter that defines a command.
For example, when the HTTP server receives a request to run a test connection, it reads the commands.cfg key for `test`
and runs the process defined by the key value, `/usr/local/bin/python app/adapter.py test`.

#### Sample Adapter:

The template adapter collects several objects and metrics from the JVM that the adapter is running in,
and can be used as a starting point for creating a new adapter.
The template adapter uses Python Integration SDK library to streamline the process of building adapter.
The template adapter has comments throughout the code to help new users understand the process of creating their own
adapter using the existing code.
For additional guidance creating adapters see our `Guides` section.

#### New Adapter:

The new adapter comes with the minimum required code to develop your own adapter. 

### Adapter methods (required)

The methods in the adapter.py source code are required, and should be modified to generate a custom adapter.
Each method fulfills a request from the VMware Aria Operations collector, and can be tested individually using
`mp-test` (covered in [Testing a Management Pack](../../get_started.md#testing-a-management-pack)).

- `test(adapter_instance)`:
  Performs a test connection using the information given to the adapter_instance to verify the adapter instance has been configured properly.
  A typical test connection will generally consist of:

  1. Read identifier values from adapter_instance that are required to connect to the target(s)
  2. Connect to the target(s), and retrieve some sample data
  3. If any of the above failed, return an error, otherwise pass.
  4. Disconnect cleanly from the target (ensure this happens even if an error occurs)

- `get_endpoints(adapter_instance)`:
  This method is run before the 'test' method, and VMware Aria Operations will use
  the results to extract a certificate from each URL. If the certificate is not trusted by
  the VMware Aria Operations Trust Store, the user will be prompted to either accept or reject
  the certificate. If it is accepted, the certificate will be added to the AdapterInstance
  object that is passed to the 'test' and 'collect' methods. Any certificate that is
  encountered in those methods should then be validated against the certificate(s)
  in the AdapterInstance. This method will only work against HTTPS endpoints, different types
  of endpoint will not work (e.g., database connections).

- `collect(adapter_instance)`:
  Performs a collection against the target host. A typical collection will generally consist of:
  1. Read identifier values from adapter_instance that are required to connect to the target(s)
  2. Connect to the target(s), and retrieve data
  3. Add the data into the CollectResult as objects, properties, metrics, etc
  4. Disconnect cleanly from the target (ensure this happens even if an error occurs)
  5. Return the CollectResult.

- `get_adapter_definition()`:
  Optional method that defines the Adapter Instance configuration. The Adapter Instance
  configuration is the set of parameters and credentials used to connect to the target and
  configure the adapter. It also defines the object types and attribute types present in a
  collection. Setting these helps VMware Aria Operations to validate, process, and display
  the data correctly. If this method is omitted, a `describe.xml` file should be manually
  created inside the `conf` directory with the same data. Generally, this is only necessary
  when using advanced features of the `describe.xml` file that are not present in this method.

!!! note

    The adapter is stateless. This means the adapter cannot store any data for use in later method calls.

