[![PyPI version](https://badge.fury.io/py/vmware_aria_operations_integration_sdk.svg)](https://badge.fury.io/py/vmware_aria_operations_integration_sdk)
[![Aria Operations Integration SDK](https://github.com/vmware/vmware-aria-operations-integration-sdk/actions/workflows/aria-operations-integration-sdk.yaml/badge.svg)](https://github.com/vmware/vmware-aria-operations-integration-sdk/actions/workflows/aria-operations-integration-sdk.yaml)
![GitHub](https://img.shields.io/github/license/vmware/vmware-aria-operations-integration-sdk?style=plastic)

VMware Aria Operations Integration SDK
=====================

Welcome to the VMware Aria Operations Integration SDK.

## What is the Integration SDK?

The Integration SDK creates Management Packs to add custom objects, data, and
relationships from an endpoint into VMware Aria Operations.

Using this SDK to create a Management Pack requires some Python or Java knowledge, 
and an understanding of how to get data from the endpoint using an API. For example, 
to create a Management Pack for Cassandra DB, an understanding of how to write an 
SQL query, execute it, and read the results is required.

Currently, installing a Management Pack built with the Integration SDK is supported for
On-Prem versions of VMware Aria Operations only, but we are working to bring support to
VMware Aria Operations Cloud in a future release.

For a high-level overview of VMware Aria Operations, Management Packs, and this SDK,
see [the introduction](introduction.md).

## What can the Integration SDK be used for?
The Integration SDK can be used to add any endpoint that supports remote monitoring to
VMware Aria Operations. Adding the endpoint involves creating objects that
represent the endpoint, which may include properties, metrics, and events, as well as
relationships between objects.

**Remote monitoring** uses an API (such as REST, SNMP, SQL, etc) to retrieve the data (as
opposed to agent-based monitoring, where the monitoring code runs in the same location
as the endpoint).

For an example walkthrough of creating a new Management Pack monitoring an endpoint, see
[Creating a new Management Pack](guides/creating_a_new_management_pack.md)

The Integration SDK can also be used to extend objects created by another Management
Pack with additional metrics, properties, events, or relationships. This can be useful
to ensure access to custom data without having to re-implement already existing data.

For an example walkthrough of the steps required to extend another management pack, see
[Extending an Existing Management Pack](guides/extending_an_existing_management_pack.md)

## Where should I start?
* If you want to get started creating your first Management Pack, or don't know where to start, read the [Get Started](get_started.md) tutorial.
* If you have completed the Get Started tutorial, the `Guides` section contains guides for modifying your adapter.

## Contributing

The vmware-aria-operations-integration-sdk project team welcomes contributions from the community. Before you start
working with this project please read and sign our [Contributor License Agreement](https://cla.vmware.com/cla/1/preview).
If you wish to contribute code and you have not signed our Contributor Licence Agreement (CLA), our bot will prompt you
to do so when you open a Pull Request. For any questions about the CLA process, please refer to our
[FAQ](https://cla.vmware.com/faq).

## License

This project is licensed under the APACHE-2 License.
