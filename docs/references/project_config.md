# Project Config File
* * *

## `connections` (array of objects)

This property stores a list of connection objects.

??? example

    ```json title="config.json" linenums="1"
    {
        "connections" : [
              {
                 ...
                }
            ]
        ...
     }
    ```

### `credential` (object)

An object that contains credential information.
??? example

    ```json title="config.json" linenums="1" hl_lines="4-11"
    {
        "connections" : [
              {
                "credential":{
                   "token": {
                       "password": true,
                       "required": true,
                       "value": "password"
                     }
                  "credential_kind_key": "my_app_credential"
                  }
                 ...
                }
            ]
        ...
     }
    ```

### `identifiers` (object)

An object that contains one or many identifiers. The identifiers should match the [adapter instance identifiers]() defined in the [Object Model]()

??? example

    ```json title="config.json" linenums="1" hl_lines="3-16"
    {
        "connections" : [
              {
                "identifiers": {
                    "container_memory_limit": {
                      "part_of_uniqueness": false,
                      "required": true,
                      "value": "2048"
                    },
                    "enable_sotrage_collection": {
                      "part_of_uniqueness": false,
                      "required": true,
                      "value": "False"
                    },
                  }
                  ...
                }
            ]
        ...
     }
    ```

### `custom_collection_number` (int, optional)

The collection number `mp-test` passes to the adapter instance. This is helpful when testing adapter behaviours
that are triggered based on collection number (for example, an expensive computation that can doesn't need to happen every collection).

??? example

    ```json title="config.json" linenums="1" hl_lines="3-16"
    {
        "connections" : [
                "custom_collection_number": 10,
                ...
            ]
        ...
    }
    ```

### `custom_collection_window` (int, optional)

The collection window duration `mp-test` passed to the adapter instance. This is helpful when testing behaviours that are triggered based on collection window duration.

### `name` (string)

The name of the connection. This is used as the connection identifier and can be used to specify a connection name when using `mp-test`.

??? example
    ```json
    {
        "connections" : [
              {
                 ...
                 name:"host-1"
              },
              {
                 ...
                 name:"host-2"
              }
            ]
        ...
     }
    ```

### `suite_api_hostname` (string)

The suite API host name used for this connection. If there isn't one, the values should be 'null'.

??? example
    ```json
    {
        "connections" : [
              {
                 ...
                suite_api_hostname: "my-host.example.com"
              }
            ]
        ...
     }
    ```

??? note

    If this property is not provided for the connection, then it will fall back to the property defined outside of the connections.

    ```json
    {
        "connections" : [
              {
                 ...
              }
            ]
        ...
        suite_api_hostname: "my-default-host.example.com",
        suite_api_password: "my_password",
        suite_api_username: "my_username",
     }
    ```

### `suite_api_password` (string)

The suite API password used to login to the specified host. If there isn't one, the values should be 'null'.

??? example
    ```json
    {
        "connections" : [
              {
                 ...
                suite_api_password: "my_password",
              }
            ]
        ...
     }
    ```

??? note

    If this property is not provided for the connection, then it will fall back to the property defined outside of the connections.

    ```json
    {
        "connections" : [
              {
                 ...
              }
            ]
        ...
        suite_api_hostname: "my-default-host.example.com",
        suite_api_password: "my_password",
        suite_api_username: "my_username",
     }
    ```

#### `suite_api_username` (string)

The suite API user name used to login to the specified host. If there isn't one, the values should be 'null'.

??? example
    ```json
    {
        "connections" : [
              {
                 ...
                suite_api_username: "my_username",
              }
            ]
        ...
     }
    ```

??? note

    If this property is not provided for the connection, then it will fall back to the property defined outside of the connections.

    ```json
    {
        "connections" : [
              {
                 ...
              }
            ]
        ...
        suite_api_hostname: "my-default-host.example.com",
        suite_api_password: "my_password",
        suite_api_username: "my_username",
     }
    ```