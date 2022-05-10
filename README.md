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

    The Management Pack display name will show up in vROps (Data Sources &rarr; Integrations &rarr;
    Repository), or when adding an account.

    ![Integration Card for the 'TestAdapter' Management Pack](doc/test-adapter-integration-card.png)

    *This Management Pack's display name is 'TestAdapter', and uses the default icon*

3. `Management Pack description`

    This field should describe what the Management Pack will do or monitor.

4. `Management Pack vendor`

    The vendor field shows up in the UI under 'About' on the Integration Card.

    ![About popup for the 'TestAdapter' Management Pack](doc/test-adapter-about.png)

    *This Management Pack's vendor is 'VMware'*

5. `Enter a path to a EULA text file, or leave blank for no EULA`

    vROps requires a EULA file to be present in a Management
    Pack. If one isn't provided, a stub EULA file (`eula.txt` in the root project directory) will be added to the project
    which reads:
    ```
    There is no EULA associated with this Management Pack.
    ```

6. `Enter a path to the Management Pack icon file, or leave blank for no icon`

    The icon is used in the vROps UI if present. If it is not present, a default icon will be used. 
    The icon file must be png format and 256x256 px. An icon file can be added later by copying the icon to the root
    project directory and setting the 

8. `Select a language for the adapter. Supported languages are [...]`

    Supported languages are listed. Once selected, the project will be generated, including a template adapter in the
    selected language. The template adapter collects several objects and metrics from the docker container that the adapter
    is running in, and can be used as a starting point for creating a new adapter.

For complete documentation of the `mp-init` tool see the [MP Initialization Tool Documentation](doc/mp-init.md).

### Testing a Management Pack
To test a project, run `mp-test`  in the virtual environment.

For complete documentation of the `mp-test` tool see the [MP Test Tool Documentation](doc/mp-test.md).

### Building and installing a Management Pack
To build a project, run `mp-build`  in the virtual environment.

For complete documentation of the `mp-build` tool see the [MP Build Tool Documentation](doc/mp-build.md).
