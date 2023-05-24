Architecture
============

This section describes how a Management Pack works, and how it interacts with the VMware 
Aria Operations Collector.

## Management Pack
A management pack consists of content, metadata, and an adapter.

* Content includes Dashboards, Reports, Icons, Symptoms, Alerts, Traversals, others.
* Metadata includes the describe.xml file that describes an adapter, and the 
  `manifest.txt` file that describes the management pack as a whole.
* The Adapter is the code that performs the collection and sends the data to VMware Aria 
  Operations.

### Adapter Container Image
The adapter container image consists of two parts:
* A REST server specified by [Collector Framework 2](../vmware_aria_operations_integration_sdk/api/vmware-aria-operations-collector-fwk2.json).
* The adapter code that performs the collection.

In an adapter created using the SDK, the REST server is provided inside a base container
image that can built upon. In the adapter's dockerfile, this is specified in the 'FROM' 
directive on the first line. This default server implements all the required endpoints, 
provides error handling, and adds some additional context to the user code that is not 
present in the original REST requests. The server also adds an additional 
[definition endpoint](../vmware_aria_operations_integration_sdk/api/integration-sdk-definition-endpoint.json)
which allows the collection code to describe itself, rather than requiring a 
`describe.xml` file to be manually created, and some features that improve the debugging
experience.

The server determines how to call the user code by reading a file called `commands.cfg` 
that is present in the Project Directory. This file provides a mapping from each 
endpoint served by the REST server to an executable command that will run as a separate 
process inside the container. Importantly, the server appends two extra arguments to 
each process call: An input and output named pipe. These are used for interprocess 
communication.

Because commands are run as a subprocess, the server is able to detect and handle many
common errors (such as the process crashing without writing a result) without affecting
the operation of the server.

Importantly, this model enforces that adapters remain stateless. Because each call 
results in a new subprocess being created, there is no way to save any state between 
calls in the runtime environment. 
Some benefits of a stateless adapter are:
* Potential for (slow) memory leaks is reduced.
* Potential for an adapter to return stale (cached) data is reduced.
* Potential for an adapter to crash or hang due to a previous collection leaving the
  adapter in an inconsistent state is reduced.
 
Note that it is possible to pass data between collections by writing and reading to a 
file on the container filesystem, but not encouraged.

![Cloud Proxy Components running two Adapter Container Images](cloud-proxy-components.png)

#### Commands.cfg
In order to support multiple languages, the REST server reads a file called 
`commands.cfg`, which is copied from the project root directory to the container. This
file contains commands to run for the different REST endpoints. The default file for
a Python adapter looks like this:
```
[Commands]
test=/usr/local/bin/python app/adapter.py test
collect=/usr/local/bin/python app/adapter.py collect
adapter_definition=/usr/local/bin/python app/adapter.py adapter_definition
endpoint_urls=/usr/local/bin/python app/adapter.py endpoint_urls
```
This can be modified if necessary. For example, by default there is a single entry 
point for all endpoints, and the correct method is called by looking at the last
argument. However, it is possible to have different entry points for the different
endpoints, or even use different languages or runtimes for different endpoints by
modifying the command that gets run for a given endpoint.

In addition, when the server calls the command listed, it always appends to extra
arguments, an input and output named pipe. The named pipes are created by the Server
inside a temporary directory that is created for each subprocess. For example, the 
server call the above test command will look similar to this:
```
/usr/local/bin/python app/adapter.py test /tmp/tmpe1iu4msr/input_pipe /tmp/tmpe1iu4msr/output_pipe
```

### Collection
When performing a collection, test connection, definition, or get endpoints request,
the following sequence takes place:
1. VMware Aria Operations Collector sends request to adapter.
2. Server reads `commands.cfg` to determine how to handle the request.
3. Server starts a subprocess with the command and arguments from `commands.cfg`, plus
   the input and output named pipe arguments.
4. Server sends the request payload to 'input' named pipe.
5. Server waits for subprocess to complete and write its response to the 'output' 
   named pipe, then reads the result.
7. Server processes the result and sends it as a response to the original REST request.
8. If any steps failed, clean up and send an appropriate error message as REST request
   response.

Note: The `mp-test` tool by default has a timeout of 5 minutes for each REST request.
This is different than the Cloud Proxy's `Adapter Handler`, which does not have any
timeout. Thus, it is possible when running on a Cloud Proxy for a collection to 
wait forever at step (5) above.

### Registry
Containerized adapters make use of an external container registry to distribute images.
The user requires push access when building a Pack File, and the VMware Aria Operations
Cloud Proxy needs anonymous pull access to the registry.

Within a Pack File, the adapter container image is referenced by the registry location
and image digest SHA.

The following diagram shows how the processes for building and installing a Management 
Pack work together with the registry.

![Building and installing a Pack File](registry.png)

