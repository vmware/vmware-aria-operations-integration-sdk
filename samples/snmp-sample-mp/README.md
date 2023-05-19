# SNMP Sample MP

## Requirements
- [Integration SDK](../../README.md#Requirements)
- vCenter Adapter Instance on VMware Aria Operations
- Container registry accessible to the cloud proxy where the vCenter MP Extension adapter will run.
 
## About the MP

This Management Pack sets up SNMP v2 or v3 credentials and runs a simple 'get' command to retrieve some basic data. It is not
intended to be useful on its own, rather it is a starting point for creating a management pack that uses SNMP.

## Building
### Build pak file
- Run `mp-build` at the root of the sample project directory. `mp-build` uses the given container registry to 
  upload a container image that contains the adapter. The cloud proxy pulls the container image from the registry and
  runs the adapter inside the container. Consult the [Troubleshooting](../../README.md#troubleshooting) section for 
  additional information about setting up container registries.

