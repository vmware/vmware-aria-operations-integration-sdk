# Connections
* * * 

### What are Connections?
A **connection** refers to the link between Integration SDK and other external systems, such as a vCenter Server, other
databases, or cloud services. These connections allow Integration SDK to gather performance and capacity data about your
virtual or physical infrastructure operations, which can then be analyzed and presented in a unified, comprehensive view. Aria
Operations uses this data to help automate and simplify operations management.

Creating a connection usually involves specifying the IP address or hostname of the external system, along with the appropriate
[credentials]() to access that system. After establishing the connection, Integration SDK can collect data from the connected system. 

### How are Connections Stored?

Connections are stored locally in a [config.json](config.json) file located at the root of every project the project.  
If no config.json file exist at the time of creating a connection, one will be created.


### Managing Connections 

### Creating New Connections 

To create a connection, simply run [mp-test](mp-test.md) and then select `New Connection`. [mp-test](mp-test.md) will then create a new connection by
parsing over the object model and using any [TODO]() and [credentials](). The new connection is then stored in the [config.json](config.json) in the root of the project. 


#### Editing Existing Connections

Connections can be edited by modifying the key-values in the [config.json](config.json) file at the root of the project that correspond to the value you want to modify.

#### Deleting Connecitons

To delete a connection remove the collection object from [config.json](config.json) file at the root of the project that correspond to the connection you want to delete.



