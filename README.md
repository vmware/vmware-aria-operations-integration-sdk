vROps Integration SDK
=====================

Welcome to the vRealize Operations Integration SDK. 

Where should I start?
* If you want to get started creating your first Management Pack, or don't know where to start, [read the get started tutorial](#Get Started).
* If you'd like an introduction to vROps, Management Packs, and this SDK, [read the introduction](doc/introduction.md).
* All documentation is available [here](doc/contents.md).

## Get Started

This guide will walk through setting up the SDK and using the SDK
to create, test, and install a simple Management Pack (integration) onto vROps.

Contents
* [Prerequisites](#prerequisites)
* [Installation](#installation)
* [First Management Pack](#creating-a-management-pack)

### Prerequisites

Note: Currently the SDK does not support Windows.

#### Requirements
The SDK requires a few prerequisites:
* Docker 20.10.13 or later. Earlier versions of 20.10 may also work, but updating to the latest stable version is recommended.
  For instructions on installing Docker, go to [Docker's installation documentation](https://docs.docker.com/engine/install/),
  choose the OS you need and follow the instructions provided.
* Python3 3.9. Earlier versions of Python3 may also work, but updating to the latest stable version is recommended. Python2 is not supported.
  For instructions on installing Python, go to [Python's installation documentation](https://wiki.python.org/moin/BeginnersGuide/Download),
  choose the OS you need and follow the instructions provided.
* Pip. If Python3 is installed, pip is most likely also installed.
  [Pip's installation documentation](https://pip.pypa.io/en/stable/installation/).
* Git. For instructions in installing git, go to [Git's installation documentation](https://git-scm.com/downloads),
  choose the OS you need and follow the instructions provided.

#### Optional Requirements
In addition, the following are optional requirements. (Note: For the Alpha, creating Java and Powershell Management Packs
is disabled)
* Java. Java is only required for building Java Management Packs. We recommend the latest version of the [Azul Zulu SDK](https://www.azul.com/downloads/?package=jdk#download-openjdk).
* Powershell. Powershell is only required for building Powershell Management Packs. See [Microsoft's installation instructions for PowerShell](https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell?view=powershell-7.2).

### Installation
```sh
git clone https://gitlab.eng.vmware.com/cmbu-tvg/vrops-python-sdk
cd vrops-python-sdk
./install.sh
```
The install script creates a config file (`~/.vrops-sdk/config.json`), generates a Python virtual environment, and
installs several tools (`mp-init`, `mp-test`, and `mp-build`) into the virtual environment. To access these tools,
activate the virtual environment:
```sh
source vrops_mp_sdk_venv/bin/activate
```
To exit the virtual environment, run `deactivate` in the virtual environment.

### Creating a Management Pack
To create a new project, run `mp-init` in the virtual environment. This tool asks a series of questions that guides
the creation of a new management pack project. 

1. `Enter a path for the project (where code for collection, metadata, and content reside)`

    The path can be an absolute path, or a path relative to the directory `mp-init` was run from. The path should end in an empty
    or non-existing directory. If the directory does not exist, it will be created. This directory will contain a new Management
    Pack project.

2. `Management Pack display name`

    The Management Pack display name will show up in vROps (**Data Sources &rarr; Integrations &rarr;
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

    vROps requires a EULA file to be present in a Management
    Pack. If one isn't provided, a stub EULA file (`eula.txt` in the root project directory) will be added to the project
    which reads:
    ```
    There is no EULA associated with this Management Pack.
    ```

7. `Enter a path to the Management Pack icon file, or leave blank for no icon`

    The icon is used in the vROps UI if present. If it is not present, a default icon will be used. 
    The icon file must be png format and 256x256 px. An icon file can be added later by copying the icon to the root
    project directory and setting the value of `"pak_icon"` to the icon's file name in the `manifest.txt` file.

8. `Select a language for the adapter. Supported languages are [...]`

    Supported languages are listed. Once selected, the project will be generated, including a template adapter in the
    selected language. The template adapter collects several objects and metrics from the docker container that the adapter
    is running in, and can be used as a starting point for creating a new adapter.

For complete documentation of the `mp-init` tool see the [MP Initialization Tool Documentation](doc/mp-init.md).

### Testing a Management Pack
To test a project, run `mp-test`  in the virtual environment.

If `mp-test` is run from anywhere outside of a root project directory, the tool will prompt to choose a project, and will
test the selected project. If the tool is run from a project directory, the tool will automatically test that
project.

`mp-test` will ask for a _connection_. No connections should exist, so choose **New Connection**. The test tool then
reads the `conf/describe.xml` file to find the connection parameters and credentials required for a connection, and prompts
for each. This is similar to creating a new _Adapter Instance_ in the vROps UI. Connections are automatically saved
per project, and can be reused when re-running the `mp-test` tool.

In the template project, the only connection parameter is `ID`, and because it connects to the container it is running on,
this parameter is not necessary; it is only there as an example, and can be set to any value. The template also implements
an example Test Connection. If a Test Connection is run (see below), with the `ID` set to the text `bad`, then the Test
Connection will fail.

The test tool also asks for the method to test. There are four options:
* Test Connection - This call tests the connection and returns either an error message if the connection failed, or an empty json object if the connection succeeded.
* Collect - This call test the collection, and returns objects, metrics, properties, events, and relationships.
* Endpoint URLs - This returns a list (possibly empty) of URLs that have distinct SSL certificates that vROps can ask the end user to import into the vROps TrustStore.
* Version - This returns the API version the adapter implements. The implementation of this method is not generally handled by the developer.

For more information on these endpoints, see the [Swagger API documentation](api/vrops-collector-fwk2-openapi.json). 
Each response is validated against the API.

For complete documentation of the `mp-test` tool see the [MP Test Tool Documentation](doc/mp-test.md).

### Building and installing a Management Pack
To build a project, run `mp-build`  in the virtual environment.

If `mp-build` is run from anywhere outside of a root project directory, the tool will prompt to choose a project, and will
build the selected project. If the tool is run from a project directory, the tool will automatically build that
project.

Once the project is selected (if necessary), the tool will build the management pack and emit a `pak` file which can be 
installed on vROps. The `pak` file will be located in the project directory.

To install the `pak` file, in vROps navigate to **Data Sources &rarr; Integrations &rarr;
Repository** and click `ADD`. Select and upload the generated `pak` file, accept the README, and install the management pack.

To configure the management pack, vROps navigate to **Data Sources &rarr; Integrations &rarr;
Accounts** and click `ADD ACCOUNT`. Select the newly-installed management pack and configure the required fields. For 
`Collector/Group`, make sure that a cloud proxy collector is selected. Click `VALIDATE CONNECTION` to test the connection. 
It should return successfully, then click `ADD`.

By default, a collection will run every 5 minutes. The first collection should happen immediately, however newly-created
objects cannot have metrics, properties, and events added to them. After the second collection, approximately five minutes
later, the objects' metrics, properties, and events should appear. These can be checked by navigating to **Environment
&rarr; Object Browser &rarr; All Objects** and expanding the Adapter and associated object types and object.

![CPU Idle Time](doc/test-adapter-cpu-idle-time.png)
*The CPU object's `idle-time` metric in a Management Pack named `QAAdapterName`.*

For complete documentation of the `mp-build` tool see the [MP Build Tool Documentation](doc/mp-build.md).

## vROps Integration SDK Examples 
As more developers adopt the vROps Integration SDK, we encourage everyone to share their work so that others can use it 
as a reference. By seeing what other developers are working on and how they are using our tools, we'll also be able to 
make decisions for the future maintenance of the project.

- [NXL ALB AVI MP](https://gitlab.eng.vmware.com/cmbu-tvg/nxl-alb-avi-mp)
