Introduction
============
## Purpose of this SDK
This SDK provides tools and libraries to aid in developing Management Packs for VMware vRealize Operations Manager 
(vROps).

## What is a Management Pack
Management Packs provide the monitoring capabilities of vROps. vROps ships with a number of built-in Management Packs, such as the vCenter Management Pack.

A Management Pack is distributed as a single file with the extension `.pak`. Inside this file is a number of components, divided into three categories:
* Adapter: The adapter is code that vROps runs on a collector (currently limited to [_Cloud Proxies_](https://docs.vmware.com/en/vRealize-Operations/8.6/com.vmware.vcom.vapp.doc/GUID-7C52B725-4675-4A58-A0AF-6246AEFA45CD.html)). The adapter is responsible for connecting to a target, creating objects with metrics, properties, and events, and adding relationships between objects.
* Metadata: There are several pieces of metadata included in a Management Pack. These tell vROps about the objects, metrics, properties, events, that the adapter can collect, as well as information about the Management Pack such as the name and version.
* Content: Optionally included in a Management Pack are pieces of content, which help the user understand and organize the data that the adapter collects. For example: dashboards, reports, symptoms and alerts, traversals, and policies.

## Overview of this SDK
### Tools
This SDK contains three main tools for developing Management Packs.
* `mp-init` Creates a new project. This creates the correct project directory structure for use with the other tools, and includes a template/sample adapter and metadata that can be modified (used as a starting point) or overwritten with new code.
* `mp-test` Creates a containerized adapter from the project, runs the container locally using docker, and simulates the vROps environment and API calls. The various entry points of the adapter can be called, and the output is validated against the vROps API and the current metadata. This tool enables rapid development by reducing the cycle time compared to installing and running on vROps for validation.
* `mp-build` Creates a containerized adapter from the project, and bundles the adapter along with any metadata and content into a Management Pack. The resulting `pak` file can be installed on a vROps box (vROps cloud is not supported). After the Management Pack has been validated on vROps, the `pak` file is also used for distribution.
### Languages
The current release supports Python as the primary language. At the heart of each adapter is a Docker image containing
an HTTP server. The SDK includes a base image containing a server implemented in Python which calls out to user-supplied
adapter code. In addition, there are extended base images for Java and PowerShell that include the same Python HTTP
server but also include Java/PowerShell runtimes. The Python server is able to call an executable written in any
language. Currently, Java and PowerShell projects are not supported by the `mp-init` tool. However, the `mp-test`
and `mp-build` tools are language-agnostic, and depend only on the correct project file structure and a working
Dockerfile that implements
the [collector framework](../vrealize_operations_integration_sdk/api/vrops-collector-fwk2-openapi.json).
### Libraries
The SDK includes a Python library that simplifies communication with vROps, and provides a model for easily creating objects, adding properties, metrics, and events to objects, and creating relationships between objects.

Similar libraries for Java and PowerShell are planned.