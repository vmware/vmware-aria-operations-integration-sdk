Examples
========

- [NXL ALB AVI MP](https://gitlab.eng.vmware.com/cmbu-tvg/nxl-alb-avi-mp)
   - A Management Pack written in python using [vrops-integration SDK](../README.md) that aims to provide a simple 
management pack template. The management pack consumes AVI's rest API and creates objects with metrics, properties, 
and relationships, to eventually send them to vROps. NXL ALB AVI also uses our [python package](../lib/python/README.md)
, an object model for interacting with the vROps containerized API, to facilitate the building of objects, metrics, 
relationships, and more.