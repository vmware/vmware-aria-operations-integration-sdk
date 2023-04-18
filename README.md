VMware Aria Operations Integration SDK
=====================

Welcome to the VMware Aria Operations Integration SDK.

## What is the Integration SDK?

The Integration SDK creates Management Packs to add custom objects, data, and
relationships from a endpoint into VMware Aria Operations.

Using this SDK to create a Management Pack requires some Python
knowledge (more languages are planned), and an understanding of how to get
data from the endpoint using an API. For example, to create a Management Pack for
Cassandra DB, an understanding of how to write an SQL query, execute it, and read the
results is required.

Currently, installing a Management Pack built with the integration SDK is supported for
On-Prem versions of VMware Aria Operations only, but we are working to bring support to
VMware Aria Operations Cloud in a future release.

For a high-level overview of VMware Aria Operations, Management Packs, and this SDK,
see [the introduction](doc/introduction.md).

## What can the Integration SDK be used for?
The Integration SDK can be used to add any endpoint that supports remote monitoring to
VMware Aria Operations. Adding the endpoint involves creating objects that
represent the endpoint, which may include properties, metrics, and events, as well as
relationships between objects.

**Remote monitoring** uses an API (such as REST, SNMP, SQL, etc) to retrieve the data (as
opposed to agent-based monitoring, where the monitoring code runs in the same location
as the endpoint).

For an example walkthrough of creating a new Management Pack monitoring an endpoint, see
[Creating a new Management Pack for Cassandra DB](#creating-a-new-management-pack--cassandra-db-)

The Integration SDK can also be used to extend objects created by another Management
Pack with additional metrics, properties, events, or relationships. This can be useful
to ensure access to custom data without having to re-implement already existing data.

For an example walkthrough of the steps required to extend another management pack, see
[Extending the Existing Management Pack for MySQL](#extending-an-existing-management-pack--mysql-)

## Where should I start?
* If you want to get started creating your first Management Pack, or don't know where to start, read the [Get Started](#get-started) tutorial.
* If you have completed the Get Started tutorial, the [walkthroughs](#walkthroughs) are guides for modifying your adapter.
* All documentation is available from the [contents](doc/contents.md) page.

## Get Started
<details>
<summary>This guide will walk through setting up the SDK and using the SDK
to create, test, and install a simple Management Pack (integration) onto VMware Aria Operations.</summary>

Contents
* [Requirements](#requirements)
* [Installation](#installation)
* [Creating a Management Pack](#creating-a-management-pack)
* [Testing a Management Pack](#testing-a-management-pack)
* [Building and Installing a Management Pack](#building-and-installing-a-management-pack)

### Requirements

#### Operating System:
The VMware Aria Operations Integration SDK has been tested in the following OSes:
* Windows 10
* Windows 11
* macOS 12 (Monterey)
* macOS 13 (Ventura)
* Debian Linux
* Fedora Linux

Other operating systems may be compatible.

#### VMware Aria Operations
The Management Packs generated by the VMware Aria Operations Integration SDK will only run on versions that supports containerized Management Packs. Currently, this is limited to on-prem installs, version 8.10 or later.
In addition, at least one Cloud Proxy (also version 8.10 or later) must be set up in VMware Aria Operations, as containerized Management Packs must be run on a Cloud Proxy collector.

#### Dependencies
* Docker 20.10.0 or later. Updating to the latest stable version is recommended. For instructions on installing Docker,
  go to [Docker's installation documentation](https://docs.docker.com/engine/install/), choose the OS you need and
  follow the instructions provided.
* Python3 3.9.0 or later. Updating to the latest stable version is recommended. Python 3.8 and earlier (including Python2) are not supported. For instructions on installing Python, go
  to [Python's installation documentation](https://wiki.python.org/moin/BeginnersGuide/Download), choose the OS you need
  and follow the instructions provided.
* Pip. If Python3 is installed, pip is most likely also installed. For instructions on installing Pip, go
  to [Pip's installation documentation](https://pip.pypa.io/en/stable/installation/), and follow the instructions
  provided.
* Git 2.35.0 or later. Updating to the latest stable version is recommended.
  For instructions in installing git, go to [Git's installation documentation](https://git-scm.com/downloads),
  choose the OS you need and follow the instructions provided.

[//]: # (TODO: Add this section back in once we support them)
[//]: # (#### Optional Prerequisites)
[//]: # (* Java. Java is only required for building Java Management Packs. We recommend the latest version of the [Azul Zulu SDK]&#40;https://www.azul.com/downloads/?package=jdk#download-openjdk&#41;.)
[//]: # (* Powershell. Powershell is only required for building Powershell Management Packs. See [Microsoft's installation instructions for PowerShell]&#40;https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell?view=powershell-7.2&#41;.)
[//]: # (> Note: Creating Java and Powershell Management Packs is disabled for the Beta)

### Installation

To install the SDK, use `pip` to install into the global Python environment, or `pipx` to install into a isolated environment.
```sh
python3 -m pip install vmware-aria-operations-integration-sdk
```

### Creating a Management Pack
After the SDK is installed, create a new project, by running `mp-init`. This tool asks a series of questions that guides
the creation of a new management pack project.


1. `Enter a directory to create the project in. This is the directory where adapter code, metadata, and content will reside. If the directory doesn't already exist, it will be created. Path:`

    The path can be an absolute path, or a path relative to the directory `mp-init` was run from. The path should end in an empty
    or non-existing directory. If the directory does not exist, it will be created. This directory will contain a new Management
    Pack project.

2. `Management Pack display name`

    The Management Pack display name will show up in VMware Aria Operations (**Data Sources &rarr; Integrations &rarr;
    Repository**), or when adding an account.

    ![Integration Card for the 'TestAdapter' Management Pack](doc/test-adapter-integration-card.png)

    *This Management Pack's display name is 'TestAdapter', and uses the default icon*

3. `Management Pack adapter key`

    This field is used internally to identify the Management Pack and Adapter Kind. By default, it is set to the
    Management Pack display name with special characters and whitespace stripped from it.

4. `Management Pack description`

    This field should describe what the Management Pack will do or monitor.

5. `Management Pack vendor`

   The vendor field shows up in the UI under 'About' on the Integration Card.

   ![About popup for the 'TestAdapter' Management Pack](doc/test-adapter-about.png)

   *This Management Pack's vendor is 'VMware'*

6. `Enter a path to a EULA text file, or leave blank for no EULA`

   VMware Aria Operations requires a EULA file to be present in a Management Pack. If one isn't provided, a stub EULA file (`eula.txt` in
   the root project directory) will be added to the project which reads:
    ```
    There is no EULA associated with this Management Pack.
    ```

7. `Enter a path to the Management Pack icon file, or leave blank for no icon`

   The icon is used in the VMware Aria Operations UI if present. If it is not present, a default icon will be used. The icon file must be
   PNG format and 256x256 pixels. An icon file can be added later by copying the icon to the root project directory and
   setting the value of the `"pak_icon"` key to the icon's file name in the `manifest.txt` file.

[//]: # (TODO: Add this section back when we support it)
[//]: # (8. `Select a language for the adapter`)
[//]: # (  selected language. The template adapter collects several objects and metrics from the container that the adapter)
[//]: # (  Once selected, the project will be generated, including a template adapter in the)
[//]: # (  is running in, and can be used as a starting point for creating a new adapter.)

For complete documentation of the `mp-init` tool including an overview of its output, see the [MP Initialization Tool Documentation](doc/mp-init.md).

### Template Project
Every new project creates a file system that has the basic project structure required to develop and build a Management Pack.
Each file and directory are discussed in depth in the [mp-init](doc/mp-init.md) documentation. `app/adapter.py` is the adapter's
entry point and the best starting point. `adapter.py` is a template adapter that collects several objects and metrics from the
container in which the adapter is running; use the template as a starting point for creating a new adapter. The template adapter
has comments throughout its code that explain what the code does and how to turn it into your adapter. The methods inside the adapter
template are required. Modify the code inside the methods to generate the desired adapter. Each method represents a single request,
and it can be tested individually using `mp-test`, which is covered in the following section. The adapter is stateless; therefore,
the adapter cannot store any data for use in later method calls. Each method is used for a different function as described below:

- test(adapter_instance):
  Performs a test connection using the information given to the adapter_instance to verify the adapter instance has been configured properly.
  A typical test connection will generally consist of:

     1. Read identifier values from adapter_instance that are required to connect to the target(s)
     2. Connect to the target(s), and retrieve some sample data
     3. If any of the above failed, return an error, otherwise pass.
     4. Disconnect cleanly from the target (ensure this happens even if an error occurs)

- get_endpoints(adapter_instance):
  This method will be run before the 'test' method, and VMware Aria Operations will use
  the results to extract a certificate from each URL. If the certificate is not trusted by
  the VMware Aria Operations Trust Store, the user will be prompted to either accept or reject
  the certificate. If it is accepted, the certificate will be added to the AdapterInstance
  object that is passed to the 'test' and 'collect' methods. Any certificate that is
  encountered in those methods should then be validated against the certificate(s)
  in the AdapterInstance. This method will not only work against HTTPS endpoints, different types
  of endpoint will not work (eg. database connections).

- collect(adapter_instance):
  Performs a collection against the target host. A typical collection will generally consist of:
    1. Read identifier values from adapter_instance that are required to connect to the target(s)
    2. Connect to the target(s), and retrieve data
    3. Add the data into a CollectResult's objects, properties, metrics, etc
    4. Disconnect cleanly from the target (ensure this happens even if an error occurs)
    5. Return the CollectResult.

- get_adapter_definition():
  Optional method that defines the Adapter Instance configuration (parameters and credentials used to connect to the target, and configure the management pack) present in a collection, and defines the object types and attribute types present in a collection. Setting these helps VMware Aria Operations to validate, process, and display the data correctly. If this method is omitted, a `describe.xml` file should be manually created inside the `conf` directory with the same data. Generally, this is only necessary when using advanced features of the `describe.xml` file that are not present in this method.


For further guidance on using the template project, consult the [Walkthroughs](../README.md#walkthroughs) section.

### Testing a Management Pack

In the Management Pack directory, the installation script writes a `requirements.txt` file containing the version of the
SDK used to generate the project, and installs the SDK into a virtual environment named `venv`. Note that the packages
in `requirements.txt` are _not_ installed into the adapter. To add a package to the adapter, specify it in the file
`adapter_requirements.txt`.

To use the SDK, navigate to the newly-generated project directory and activate the virtual environment:

For Mac and Linux:
```sh
source venv/bin/activate
```
(This script is written for the bash shell. If you use the csh or fish shells, there are alternate activate.csh and activate.fish scripts you should use instead.)
For Windows:
```cmd
venv\Scripts\activate.bat
```
To exit the virtual environment, run `deactivate` in the virtual environment.

To test a project, run `mp-test`  in the virtual environment.

If `mp-test` is run from anywhere outside of a root project directory, the tool will prompt to choose a project, and will
test the selected project. If the tool is run from a project directory, the tool will automatically test that project.

`mp-test` will ask for a _connection_. No connections should exist, so choose **New Connection**. The test tool then
reads the `conf/describe.xml` file to find the connection parameters and credentials required for a connection, and
prompts for each. This is similar to creating a new _Adapter Instance_ in the VMware Aria Operations UI. Connections are automatically
saved per project, and can be reused when re-running the `mp-test` tool.

> Note: In the template project, the only connection parameter is `ID`, and because it connects to the container it is running on, this parameter is not necessary; it is only there as an example, and can be set to any value. The template also implements an example Test Connection. If a Test Connection is run (see below), with the `ID` set to the text `bad`, then the Test Connection will fail.

The test tool also asks for the method to test. There are four options:

* Test Connection - This call tests the connection and returns either an error message if the connection failed, or an
  empty json object if the connection succeeded.
* Collect - This call test the collection, and returns objects, metrics, properties, events, and relationships.
* Endpoint URLs - This returns a list (possibly empty) of URLs that have distinct SSL certificates that VMware Aria Operations can ask
  the end user to import into the TrustStore.
* Version - This returns
  the [VMware Aria Operations Collector API](vmware_aria_operations_integration_sdk/api/vmware-aria-operations-collector-fwk2.json) version the
  adapter implements. The implementation of this method is not generally handled by the developer.

For more information on these endpoints, see
the [Swagger API documentation](vmware_aria_operations_integration_sdk/api/vmware-aria-operations-collector-fwk2.json). Each
response is validated against the API.

For complete documentation of the `mp-test` tool see the [MP Test Tool Documentation](doc/mp-test.md).

### Building and Installing a Management Pack
To build a project, run `mp-build`  in the virtual environment.

If `mp-build` is run from anywhere outside of a root project directory, the tool will prompt to choose a project, and will
build the selected project. If the tool is run from a project directory, the tool will automatically build that
project.

Once the project is selected (if necessary), the tool will build the management pack and emit a `pak` file which can be
installed on VMware Aria Operations. The `pak` file will be located in the project directory.

To install the `pak` file, in VMware Aria Operations navigate to **Data Sources &rarr; Integrations &rarr;
Repository** and click `ADD`. Select and upload the generated `pak` file, accept the README, and install the management pack.

To configure the management pack, VMware Aria Operations navigate to **Data Sources &rarr; Integrations &rarr;
Accounts** and click `ADD ACCOUNT`. Select the newly-installed management pack and configure the required fields. For
`Collector/Group`, make sure that a cloud proxy collector is selected. Click `VALIDATE CONNECTION` to test the connection.
It should return successfully, then click `ADD`.

By default, a collection will run every 5 minutes. The first collection should happen immediately, however newly-created
objects cannot have metrics, properties, and events added to them. After the second collection, approximately five
minutes later, the objects' metrics, properties, and events should appear. These can be checked by navigating to **
Environment &rarr; Object Browser &rarr; All Objects** and expanding the Adapter and associated object types and object.

![CPU Idle Time](doc/test-adapter-cpu-idle-time.png)
*The CPU object's `idle-time` metric in a Management Pack named `QAAdapterName`.*

For complete documentation of the `mp-build` tool see the [MP Build Tool Documentation](doc/mp-build.md).
</details>

## Walkthroughs

### Creating a New Management Pack (Cassandra-DB)
<details><summary>
This guide assumes you have already set up the SDK and know how to create a new project.
It walks you through the steps necessary to monitor an endpoint, using Cassandra DB as
an example.</summary>
TODO
</details>

### Extending an Existing Management Pack (MySQL)
<details><summary>
This guide assumes you have already set up the SDK and know how to create a new project.
It walks you through the steps necessary to extend an existing Management Pact to add
additional data, using the MySQL Management Pack as an example.</summary>
TODO
</details>

--
# Troubleshooting

If you encounter any issues while using the VMware Aria Operations Integration SDK tools, you can refer to the troubleshooting guides for each tool:

- [mp-test Troubleshooting Guide](doc/mp-test.md#troubleshooting)
- [mp-init Troubleshooting Guide](doc/mp-init.md#troubleshooting)
- [mp-build Troubleshooting Guide](doc/mp-build.md#troubleshooting)

## Docker Issues
<details>

### Cannot connect to docker daemon (Windows)?
<details>
If you're having trouble getting Docker to run on your system, you can refer to the Docker documentation for instructions on how to start Docker on [macOS](https://docs.docker.com/docker-for-mac/install/), [Linux](https://docs.docker.com/desktop/install/debian/#launch-docker-desktop), and [Windows 10 and 11](https://docs.docker.com/desktop/install/windows-install/#start-docker-desktop).
</details>

### Permission denied while trying to connect to the Docker daemon?
<details>
If you're having trouble with permissions on a Windows system, you can refer to the Docker documentation for instructions on how to [Understand permission requirements for Windows](https://docs.docker.com/desktop/windows/permission-requirements/).
</details>

</details>

## Registry Issues:
<details>
TODO:
</details>

## Dockerfile Issues:
<details>
TODO:
</details>

## Adapter:
<details>

### Where are the adapter logs stored locally?
<details>
Logs are generated and stored in the `logs` directory whenever the adapter runs locally using' mp-test'
</details>

### Where the adapter logs stored VMware Aria Operations?
<details>
Logs are generated and stored in the cloud proxy at `$ALIVE_BASE/user/log/adapter/<ADAPTERNAME>_adapter3/<ADAPTER_INTERNAL_INSTANCE_ID>`. ADAPTERNAME should match the name of the adapter used in the manifest.txt, and the ADAPTER_INTERNAL_INSTANCE_ID should match the Internal ID found in VMware Aria Operations at Environment>Inventory>Adapter Instances>My Adapter Adapter Instance>Instance** in the rightmost column.
</details>

### What are the different log files?
<details>
There are five types of log files: adapter, server, build, test, and validation logs. Each log file is prepended with the type of
log file followed by a number that represents rollover.

- server.log:
Contains all logs related to the HTTP sever inside the container. Server logs can't be modified since the server code comes packaged
inside the [base-adapter image](https://projects.registry.vmware.com/harbor/projects/46752/repositories/base-adapter/artifacts-tab) Python image.

- adapter.log
Contains all logs related to the adapter

- test.log
Contains all logs related to `mp-test`

- build.log
Contains all logs related to `mp-build`

- validation.log
Contains all logs related to the validation of the collection result(s).

  Adapter logs are all the logs generated by adapter code (e.g., the test() method or the collect() methods inside
`app/adapter.py`). Finally, test logs come from the logs generated by `mp-test`.

</details>

### How do I add logs to my adapter?
<details>
The template adapter defines a logger variable which configures all logging for the adapter using [adapter_logging](https://github.com/vmware/vmware-aria-operations-integration-sdk/blob/main/lib/python/src/aria/ops/adapter_logging.py) from the python SDK. To use the logger in any other files, import the python [logging](https://docs.python.org/3/library/logging.html) module. eg.

```python3
import logging

logger = logging.getLogger(__name__)

def my_method():
  logger.info("info log")
  logger.warning("warning log")
  logger.error("error log")
  logger.debug("debug log")
   ...
```
</details>


### How do I change the log level (Server and Adapter)?
<details>

Server and Adapter log levels are set inside the `loglevels.cfg`; this file is located in the same directory where the logs are generated.
If the file does not exist, it will be generated after a collection/test collection.
</details>


### 500 INTERNAL SERVER ERROR:
<details>

Internal sever can happen for various reasons; however, the most common reason is due to an unhandled exception or syntax errors in
the adapter code. Check the server logs for clues about the issue. In some cases the issue may be detected by using `mp-test` and
going over the terminal output.
</details>


### Collection Failed (200 response to server with error)
<details>
TODO:
</details>

</details>

TODO:
### VMware Aria Operations:
TODO:
- Installation Issues
TODO:
  - Anonymous Docker Pull
TODO:
  - Unable to pull image (private container repo)
TODO:
- Adapter collection errors
TODO:
  - Setting debug level on CP
TODO:
  - Matching adapter to running containers
TODO:

## Contributing

The vmware-aria-operations-integration-sdk project team welcomes contributions from the community. Before you start
working with this project please read and sign our Contributor License Agreement (https://cla.vmware.com/cla/1/preview).
If you wish to contribute code and you have not signed our Contributor Licence Agreement (CLA), our bot will prompt you
to do so when you open a Pull Request. For any questions about the CLA process, please refer to our
[FAQ](https://cla.vmware.com/faq).

## License

This project is licensed under the APACHE-2 License.
