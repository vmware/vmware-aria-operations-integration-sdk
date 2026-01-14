![Website](https://img.shields.io/website?down_color=red&down_message=offline&up_color=green&up_message=online&url=https%3A%2F%2Fvmware.github.io%2Fvmware-aria-operations-integration-sdk%2F)
[![PyPI version](https://badge.fury.io/py/vmware_aria_operations_integration_sdk.svg)](https://badge.fury.io/py/vmware_aria_operations_integration_sdk)
[![Aria Operations Integration SDK](https://github.com/vmware/vmware-aria-operations-integration-sdk/actions/workflows/aria-operations-integration-sdk.yaml/badge.svg)](https://github.com/vmware/vmware-aria-operations-integration-sdk/actions/workflows/aria-operations-integration-sdk.yaml)
![GitHub](https://img.shields.io/github/license/vmware/vmware-aria-operations-integration-sdk?style=plastic)

VMware Cloud Foundation Operations Integration SDK
=====================

Welcome to the VMware Cloud Foundation (VCF) Operations Integration SDK.

## What is the Integration SDK?

The Integration SDK creates Management Packs to add custom objects, data, and
relationships from an endpoint into VCF Operations.

Using this SDK to create a Management Pack requires some Python or Java
knowledge, and an understanding of how to get data from the endpoint using an 
API. For example, to create a Management Pack for Cassandra DB, an understanding 
of how to write an SQL query, execute it, and read the results is required.

For a high-level overview of VCF Operations, Management Packs, and this SDK,
see [the introduction](https://vmware.github.io/vmware-aria-operations-integration-sdk/sdk/latest/introduction/).

## What can the Integration SDK be used for?
The Integration SDK can be used to add any endpoint that supports remote monitoring to
VCF Operations. Adding the endpoint involves creating objects that
represent the endpoint, which may include properties, metrics, and events, as well as
relationships between objects.

**Remote monitoring** uses an API (such as REST, SNMP, SQL, etc) to retrieve the data (as
opposed to agent-based monitoring, where the monitoring code runs in the same location
as the endpoint).

For an example walkthrough of creating a new Management Pack monitoring an endpoint, see
[Creating a New Management Pack](https://vmware.github.io/vmware-aria-operations-integration-sdk/sdk/latest/guides/creating_a_new_management_pack/)

For an example of Management Pack, see [vCommunity MP](https://github.com/vmbro/VCF-Operations-vCommunity/tree/main) by [Onur Yuzseven](https://www.linkedin.com/in/oyuzseven/). 

The Integration SDK can also be used to extend objects created by another Management
Pack with additional metrics, properties, events, or relationships. This can be useful
to ensure access to custom data without having to re-implement already existing data.

For an example walkthrough of the steps required to extend another management pack, see
[Extending an Existing Management Pack](https://vmware.github.io/vmware-aria-operations-integration-sdk/sdk/latest/guides/extending_an_existing_management_pack/)

## Where should I start?
* If you want to get started creating your first Management Pack, or don't know where to start, read the [Get Started](https://vmware.github.io/vmware-aria-operations-integration-sdk/sdk/latest/get_started/) tutorial, or jump to a specific section:
    * [Requirements](https://vmware.github.io/vmware-aria-operations-integration-sdk/sdk/latest/get_started/#requirements)
    * [Installation](https://vmware.github.io/vmware-aria-operations-integration-sdk/sdk/latest/get_started/#installation)
    * [Creating a Management Pack](https://vmware.github.io/vmware-aria-operations-integration-sdk/sdk/latest/get_started/#creating-a-management-pack)
    * [Testing a Management Pack](https://vmware.github.io/vmware-aria-operations-integration-sdk/sdk/latest/get_started/#testing-a-management-pack)
    * [Building and Installing a Management Pack](#https://vmware.github.io/vmware-aria-operations-integration-sdk/sdk/latest/get_started/building-and-installing-a-management-pack)
* If you have completed the Get Started tutorial, the `Guides` in our website have walk-throughs on how [create a new management pack](https://vmware.github.io/vmware-aria-operations-integration-sdk/sdk/latest/guides/creating_a_new_management_pack/), [extend an existing management pack](https://vmware.github.io/vmware-aria-operations-integration-sdk/guides/extending_an_existing_management_pack/) and more.
* All documentation is available at [https://vmware.github.io/vmware-aria-operations-integration-sdk/sdk/latest/](https://vmware.github.io/vmware-aria-operations-integration-sdk/).
## Contributing

The vmware-VCF-operations-integration-sdk project team welcomes contributions from the community. Before you start
working with this project please read and sign our [Contributor License Agreement](https://cla.vmware.com/cla/1/preview).
If you wish to contribute code, and you have not signed our Contributor Licence Agreement (CLA), our bot will prompt you
to do so when you open a Pull Request. For any questions about the CLA process, please refer to our
[FAQ](https://cla.vmware.com/faq).

For additional information about contributing, go to the [contributing section](contributing/README.md)

## License

This project is licensed under the APACHE-2 License.
