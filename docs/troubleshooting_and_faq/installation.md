# Installation Issues

### Management Pack fails to install
Management Packs can fail to install for a number of reasons, although it is not common. 
The best way to diagnose what is happening is to look in the logs on the main VMware 
Aria Operations cluster node (not a Cloud Proxy). There are two methods to access these 
logs:
  * Using `ssh`: `ssh` into the cluster and navigate to `$ALIVE_BASE/user/log`. 
    Installation issues are logged to the analytics log, which has the form 
    `analytics-<GUID>.log`. Generally, a good place to start is to search that log file 
    for the adapter kind key (found in the `manifest.txt` file in the project directory, 
    as the entry in the `adapter_kinds` array).
  * Using the VMware Aria Operations UI: Navigate to `Administration` &rarr; 
    `Support Logs`. Expand the first `VMware Aria Operations Cluster Node`, and expand 
    `ANALYTICS`. Select the analytics log, which has the form `analytics-<GUID>.log`. 
    By default, the viewer only displays 1000 lines of the file. You may need to 
    increase this. To search, use your browser's search function.

### Adding an Account: 'Collector is not compatible with adapter type.'
![Example of a 'Collector is not compatible with adapter type' error message](../images/not_compatible.png)
> Example of a 'Collector is not compatible with adapter type' error message
> 
This message occurs if the `Collector/Group` field in the 'Add Account' page is set to a collector that is not a Cloud Proxy.
Integration SDK management packs can only run on a Cloud Proxy. See [below](#how-can-i-install-a-cloud-proxy-in-my-vmware-aria-operations-environment)
for instructions on installing a Cloud Proxy in VMware Aria Operations.

### Adding an Account: 'Unknown adapter type'

![Example of an 'Unknown Adapter Type' error message for an adapter with type/key 'Testserver'](../images/unknown_adapter_type.png)
> Example of an 'Unknown Adapter Type' error message for an adapter with type/key 'Testserver'.

This message can occur for several reasons:
- The Collector/Group the MP is running on is a Cloud Proxy. See [below](#how-can-i-install-a-cloud-proxy-in-my-vmware-aria-operations-environment)
  for instructions on installing a Cloud Proxy in VMware Aria Operations.
- Check that the Cloud Proxy version supports containerized adapters. Containerized adapter
  support was added in VMware Aria Operations version 8.10.0.

### How can I install a Cloud Proxy in my VMware Aria Operations environment?

For instructions for setting up a Cloud Proxy, see
[this document](https://docs.vmware.com/en/VMware-Aria-Operations/8.12/Configuring-Operations/GUID-7C52B725-4675-4A58-A0AF-6246AEFA45CD.html).
