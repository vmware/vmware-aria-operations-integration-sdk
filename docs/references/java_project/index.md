# Java Projects

When you choose Java as the language for your project,
[mp-init](../mp-init.md) will generate a project structure tailored for writing Adapters using Java.
A Java-based project structure uses Gradle for dependency management and the [Java Adapter Library](java_lib/index.html)
to streamline the Adapter development process. 

## Dependencies:

- Azul Zulu JDK 17.
  Java Adapters compile and run within a container,
  so a JDK is not strictly necessary, but it is generally useful for development.
  The container is built with Zulu JDK 17, so ideally this version should be used for maximum compatibility.
  To access the most recent Zulu JDK 17 release,
  visit [azul.com](https://www.azul.com/downloads/?version=java-17-lts&package=jdk#zulu).


## Project Structure 

All the templates generate the [base project structure](../mp-init.md#base-project-structure) along with some additional
files and directories specific to Java (highlighted below): 

``` hl_lines="3 4 35-38"
.
├── Dockerfile
├── build.gradle.kts
├── commands.cfg
├── connections.json
├── eula.txt
├── manifest.txt
├── requirements.txt
├── conf
│   ├── describeSchema.xsd
│   └──  images
│       ├── AdapterKind
│       ├── ResourceKind
│       └── TraversalSpec
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
├── resources
│   └── resources.properties
└── src
    └── com
        └── mycompany
            └── Adapter.java
```

src (directory)
: This directory contains the package structure specified during `mp-init`. 
  Inside the package, there is an `Adapter.java` file that serves as the main class for the project. 

build.gradle.kts (file)
: This file tells the Java Compiler how to build the project, including all of the dependencies and where to find them.
  Additionally, there is a custom `generateDependencies` task that is used by the multi-stage Dockerfile for
  creating the final Adpater Conatainer Image. This task should not be modified, and it should not be removed as a dependency
  of the `jar` task.

commands.cfg (file)
: This file contains a list of the commands the HTTP server can run, along with the path to the executable related to the
  command. By default, all commands are run by executing the compiled jar (with dependencies) file along with a parameter 
  that defines a command.  For example, when the HTTP server receives a request to run a test connection, it reads the 
  commands.cfg key for `test` and runs the process defined by the key value, 
  `/usr/bin/java -cp app.jar:dependencies/* {package_name}.Adapter test`.

---
## Templates
### Sample Adapter

The template adapter collects several objects and metrics from the JVM that the adapter is running in,
and can be used as a starting point for creating a new adapter. 
The template adapter uses Java Integration SDK library to streamline the process of building adapter.
The template adapter has comments throughout the code to help new users understand the process of creating their own
adapter using the existing code. 
For additional guidance creating adapters see our `Guides` section.

### New Adapter

The new adapter comes with the minimum required code to develop your own adapter.

## Adapter Methods

The methods in the Adapter.java source code are required, and should be modified to generate a custom adapter.
Each method fulfills a request from the
VCF Operations collector, and can be tested individually
using`mp-test` (covered in [Testing a Management Pack](../../get_started.md#testing-a-management-pack)).

`public CollectResult test(AdapterInstance adapterInstance)`
:   Performs a test connection using the information given to the adapterInstance to verify the adapter instance has been configured properly.
    A typical test connection will generally consist of:
  
    1. Read identifier values from adapterInstance that are required to connect to the target(s)
    2. Connect to the target(s), and retrieve some sample data
    3. If any of the above failed, return an error, otherwise pass.
    4. Disconnect cleanly from the target (ensure this happens even if an error occurs)
  
`public CollectResult getEndpoints(AdapterInstance adapterInstance)`:
:   This method is run before the 'test' method, and VCF Operations will use
    the results to extract a certificate from each URL. If the certificate is not trusted by
    the VCF Operations Trust Store, the user will be prompted to either accept or reject
    the certificate. If it is accepted, the certificate will be added to the AdapterInstance
    object that is passed to the 'test' and 'collect' methods. Any certificate that is
    encountered in those methods should then be validated against the certificate(s)
    in the AdapterInstance. This method will only work against HTTPS endpoints, different types
    of endpoint will not work (e.g., database connections).
  
  `public CollectResult collect(AdapterInstance adapterInstance)`:
:   Performs a collection against the target host. A typical collection will generally consist of:

    1. Read identifier values from adapterInstance that are required to connect to the target(s)
    2. Connect to the target(s), and retrieve data
    3. Add the data into the CollectResult as objects, properties, metrics, etc
    4. Disconnect cleanly from the target (ensure this happens even if an error occurs)
    5. Return the CollectResult.
  
`public AdapterDefinition getAdapterDefinition()`:
:   Optional method that defines the Adapter Instance configuration. The Adapter Instance
    configuration is the set of parameters and credentials used to connect to the target and
    configure the adapter. It also defines the object types and attribute types present in a
    collection. Setting these helps VCF Operations to validate, process, and display
    the data correctly. If this method is omitted, a `describe.xml` file should be manually
    created inside the `conf` directory with the same data. Generally, this is only necessary
    when using advanced features of the `describe.xml` file that are not present in this method.

!!! note

    The adapter is stateless. This means the adapter cannot store any data for use in later method calls.
