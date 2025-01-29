Examples
========


- [Alibaba Cloud MP](https://github.com/vmware/vmware-aria-operations-integration-sdk/tree/main/samples/alibaba-cloud-mp)
    - This Management Pack collects some data about Alibaba Cloud ECS Instances and Security Groups. This Management
      Pack has a [walkthrough](guides/creating_a_new_management_pack.md) guide that shows how to create a new Management Pack.

- [MySQL Extension MP](https://github.com/vmware/vmware-aria-operations-integration-sdk/tree/main/samples/mysql-extension-mp)
      - A Management Pack collects some data from MySQL and attaches them to objects created by the MySQL Management
      Pack. This Management Pack has a [walkthrough](guides/extending_an_existing_management_pack.md) on how to extend an existing Management Pack.

- [MySQL Extension Java MP](https://github.com/vmware/vmware-aria-operations-integration-sdk/tree/main/samples/mysql-extension-java-mp)
      - This is the same Management Pack as above but written in Java.  This Management Pack can be used with the 
      [walkthrough](guides/extending_an_existing_management_pack.md) on how to extend an existing Management Pack, with
      some modifications for using Java instead of Python.

- [vCenter Extension MP](https://github.com/vmware/vmware-aria-operations-integration-sdk/tree/main/samples/vcenter-extension-mp)
      - A Management Pack written in Python that collects some additional Host and VM data from vCenter and attaches 
      them to the corresponding objects created by the vCenter Management Pack.

Templates
=========

- [REST Template](https://github.com/vmware/vmware-aria-operations-integration-sdk/tree/main/samples/rest-template-mp)
    - This Management Pack queries a simple REST API. It is designed to be used as a template for how to perform REST calls,
    parse the results, and send back data to VCF Operations. It can be used as a reference or as a starting point for
    a new Management Pack.

- [SNMP Template](https://github.com/vmware/vmware-aria-operations-integration-sdk/tree/main/samples/snmp-template-mp)
    - This Management Pack queries SNMP for some basic data. It is designed to be used as a template for how to perform 
    SNMP calls, parse the results, and send back data to VCF Operations. It can be used as a reference or as a starting
    point for a new Management Pack.

[//]: # (- [NSX ALB AVI MP]&#40;https://gitlab.eng.vmware.com/cmbu-tvg/nxl-alb-avi-mp&#41;)
[//]: # (   - a management pack written in python using the [vmware aria operations integration sdk]&#40;../readme.md&#41; that aims to )
[//]: # (     provide a simple management pack template. the management pack consumes nsx alb avi's rest api and creates objects )
[//]: # (     with metrics, properties, and relationships, to eventually send them to vmware aria operations. nsx alb avi )
[//]: # (     management pack also uses our [python package]&#40;../lib/python/readme.md&#41;, an object model for interacting with the )
[//]: # (     vmware aria operations containerized integration api, to facilitate the building of objects, metrics, )
[//]: # (     relationships, and more. for more information about nsx alb, visit vmware's )
[//]: # (     [product page for nsx alb]&#40;https://www.vmware.com/products/nsx-advanced-load-balancer.html&#41;.)
