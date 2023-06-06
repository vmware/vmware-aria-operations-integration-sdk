# Connections
* * *

### What are Connections?
A **connection** refers to the link between an Adapter and other external systems, such as a vCenter Server, other
databases, or cloud services. These connections allow an Adapter to gather performance and capacity data about your
virtual or physical infrastructure operations, which can then be analyzed and presented in a unified, comprehensive view. VMware Aria
Operations uses this data to help automate and simplify operations management.

Creating a connection usually involves specifying the IP address or hostname of the external system, along with the appropriate
[credentials]() to access that system. After establishing the connection, an Adapter can collect data from the connected system.

### How are Connections Stored?

Connections are stored locally in a [project config file](project_config.md) file located at the root of every project the project.
If no project config file file exist at the time of creating a connection, one will be created.


### Managing Connections

#### Creating New Connections

To create a connection, run `mp-test` and then select `New Connection`. [mp-test](mp-test.md) will then create a new connection by
parsing over the object model and using any [identifiers](../guides/adding_to_an_adapter.md#defining-an-adapter-and-adapter-instance-in-the-object-model)
and [credentials](../guides/adding_to_an_adapter.md#defining-a-credential-in-the-object-model). The new connection is then stored in the
[project config file](project_config.md) in the root of the project.


#### Editing Existing Connections

Connections can be edited by modifying the key-values in the [project config file](project_config.md) file at the root of the project that correspond to the value you want to modify.

??? example

    To edit the `container_memory_limit`  for connection with name `large-memory`, we can edit the key-value for
    `container_memory_limit` inside the connection object (line 71).

    ```json title="config.json" linenums="1" hl_lines="71"
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

#### Deleting Connecitons

To delete a connection remove the collection object from [project config file](project_config.md) file at the root of the project that correspond to the connection you want to delete.

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
