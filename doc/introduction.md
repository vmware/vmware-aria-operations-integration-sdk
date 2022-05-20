Introduction
============
## Purpose of this SDK

This SDK provides tools and libraries to aid in developing Management Packs for VMware vRealize Operations Manager 
(VMware vROps).

## What is a Management Pack

A Management Pack extends the monitoring capabilities of vROps. Management Packs run on a _collector_ in vROps.

A Management Pack is distributed as a single file with the extension `.pak`. Inside this file is a number of components, divided into three categories:
* Adapter: The adapter is code that vROps runs on its _collector_. The adapter is responsible for connecting to a target, creating objects with metrics, properties, and events, and adding relationships between objects.
* Metadata: There are several pieces of metadata included in a Management Pack. These tell vROps about the objects, metrics, properties, events, that the adapter can collect, as well as information about the Management Pack such as the name and version.
* Content: Optionally included in a Management Pack are pieces of content, which help the user understand and organize the data that the adapter collects. For example: dashboards, reports, symptoms and alerts, traversals, policies.

## Overview of this SDK
### Tools
This SDK contains three main tools for developing Management Packs.
* `mp-init` Creates a new project. This creates the correct project directory structure for use with the other tools, and includes a template/sample adapter and metadata that can be modified (used as a starting point) or overwritten with new code.
* `mp-test` Compiles the project into an adapter, which runs in a docker container and simulates the vROps environment and API calls. The various entry points of the adapter can be called, and the output is validated against the vROps API and the current metadata. This tool enables rapid development by reducing the cycle time compared to installing and running on vROps for validation.
* `mp-build` Compiles the project into an adapter, and bundles the adapter along with any metadata and content into a Management Pack. The resulting `pak` file can be installed on a vROps box (vROps cloud is not supported). After the Management Pack has been validated on vROps, the `pak` file is also used for distribution.
### Libraries
The SDK includes a Python library that simplifies communication with vROps, and provides a model for easily creating objects, adding properties, metrics, and events to objects, and creating relationships between objects.
### Languages
The current release supports Python as the primary language. PowerShell and Java are planned for future releases. However, any language can be used with the `mp-test` and `mp-build` tools included in the SDK.