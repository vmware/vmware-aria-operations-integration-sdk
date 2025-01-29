# Connections
* * *

### What are Connections?
A **connection** refers to the link between an Adapter and other external systems, such as a vCenter Server, other
databases, or cloud services. These connections allow an Adapter to gather performance and capacity data about your
virtual or physical infrastructure operations, which can then be analyzed and presented in a unified, comprehensive view. VMware
Cloud Foundation (VCF) Operations uses this data to help automate and simplify operations management.

Creating a connection usually involves specifying the IP address or hostname of the external system, along with the appropriate
[credentials](../guides/adding_to_an_adapter.md#defining-a-credential-in-the-object-model) to access that system.
After establishing the connection, an Adapter can collect data from the connected system.

!!! warning

    Credentials for connections are stored in plain text in the 
    [project connections file](project_connections_config.md). For this reason, we recommend that this 
    file is not included in version control (it is included in the .gitignore file by 
    default), and credentials should be revokable and have the minimum set of
    permissions necessary for the Adapter to function (Usually Read-Only is sufficient).

In addition, sometimes it is desirable for an Adapter to query VCF Operations' 
`SuiteAPI`. To facilitate using the API, credentials and connection information are 
automatically provided to the Adapter when running on a Cloud Proxy. To mimic this when 
running locally using `mp-test`, `mp-test` needs the SuiteAPI hostname, username, and 
password.

??? note

    Suite API documentation can be found on any VCF Operations Cluster, by
    opening `https://[[vmware_aria_operations_cluster_hostname]]/suite-api/doc/swagger-ui.html`. 

When setting up a new connection, `mp-test` will ask if you want to set up the connection
information for the SuiteAPI. If you are not using this functionality, this can be 
skipped, otherwise, the hostname should be the VCF Operations Cluster hostname, 
and the username and password can be any user with permission to access the Suite API.
`mp-test` will also prompt if you want to set the SuiteAPI credentials as the project 
default. If you select 'yes', then every connection in this project will use the 
provided credentials, unless they explicitly override them. To learn more about how 
Suite API connections are handled, see the 
[project connections file](project_connections_config.md#suiteapihostname-string) documentation.

### How are Connections Stored?

Connections are stored locally in the [project connections file](project_connections_config.md)
located in the root of the project.
If no project config file exists at the time of creating a connection, one will be created.


### Managing Connections

#### Creating New Connections

To create a connection, run `mp-test` and then select `New Connection`. [mp-test](mp-test.md) will then create a new connection by
parsing over the object model and using any [identifiers](../guides/adding_to_an_adapter.md#defining-an-adapter-and-adapter-instance-in-the-object-model)
and [credentials](../guides/adding_to_an_adapter.md#defining-a-credential-in-the-object-model). The new connection is then stored in the
[project connections file](project_connections_config.md) in the root of the project.


#### Editing Existing Connections
To edit connections,
simply modify the key-values in the [project connections file](project_connections_config.md)
located at the project's root that correspond to the value you want to change.

??? example

    To edit the `container_memory_limit`  for connection with name `large-memory`, we can edit the key-value for
    `container_memory_limit` inside the connection object (line 44).

    ```json title="config.json" linenums="1" hl_lines="44"
    {
      "connections": [
          {
              "certificates": [],
              "credential": {},
              "custom_collection_number": null,
              "custom_collection_window": null,
              "identifiers": {
                  "host": {
                      "part_of_uniqueness": true,
                      "required": true,
                      "value": "example.com"
                  },
                  "container_memory_limit": {
                      "part_of_uniqueness": false,
                      "required": true,
                      "value": "512"
                  },
                  "port": {
                      "part_of_uniqueness": true,
                      "required": true,
                      "value": "443"
                  }
              },
              "name": "small-memory",
              "suite_api_hostname": null,
              "suite_api_password": null,
              "suite_api_username": null
          },
          {
              "certificates": [],
              "credential": {},
              "custom_collection_number": null,
              "custom_collection_window": null,
              "identifiers": {
                  "api": {
                      "part_of_uniqueness": true,
                      "required": true,
                      "value": "ecample.com"
                  },
                  "container_memory_limit": {
                      "part_of_uniqueness": false,
                      "required": true,
                      "value": "4096"
                  },
                  "port": {
                      "part_of_uniqueness": true,
                      "required": true,
                      "value": "443"
                  }
              },
              "name": "large-memory",
              "suite_api_hostname": null,
              "suite_api_password": null,
              "suite_api_username": null
          }
      ],
      "default_memory_limit": 1024,
      "docker_port": 8080,
      "suite_api_hostname": "hostname",
      "suite_api_password": "password",
      "suite_api_username": "username"
    }

    ```

#### Deleting Connections

To delete a connection,
remove the connection object from the `connections` list in the [project connections file](project_connections_config.md)
at the root of the project that corresponds to the connection you want to delete.

??? example

    To remove the connection with name `medium-memory`, we can delete the highlighted connection object


    ```json title="config.json" linenums="1" hl_lines="30-56"
    {
      "connections": [
          {
              "certificates": [],
              "credential": {},
              "custom_collection_number": null,
              "custom_collection_window": null,
              "identifiers": {
                  "host": {
                      "part_of_uniqueness": true,
                      "required": true,
                      "value": "example.com"
                  },
                  "container_memory_limit": {
                      "part_of_uniqueness": false,
                      "required": true,
                      "value": "512"
                  },
                  "port": {
                      "part_of_uniqueness": true,
                      "required": true,
                      "value": "443"
                  }
              },
              "name": "small-memory",
              "suite_api_hostname": null,
              "suite_api_password": null,
              "suite_api_username": null
          },
          {
              "certificates": [],
              "credential": {},
              "custom_collection_number": null,
              "custom_collection_window": null,
              "identifiers": {
                  "api": {
                      "part_of_uniqueness": true,
                      "required": true,
                      "value": "example.com"
                  },
                  "container_memory_limit": {
                      "part_of_uniqueness": false,
                      "required": true,
                      "value": "1024"
                  },
                  "port": {
                      "part_of_uniqueness": true,
                      "required": true,
                      "value": "443"
                  }
              },
              "name": "medium-memory",
              "suite_api_hostname": null,
              "suite_api_password": null,
              "suite_api_username": null
          },
      ],
      "default_memory_limit": 1024,
      "docker_port": 8080,
      "suite_api_hostname": "hostname",
      "suite_api_password": "password",
      "suite_api_username": "username"
    }

    ```
