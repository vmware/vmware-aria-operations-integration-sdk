# Global Config File
* * *

### `default_container_registry_path` (string, optional)

Specifies the default container registry path
to be used by [mp-build](mp-build.md) any time
the [project config file](project_config.md#containerrepository-string) doesn't contain a [container_repository](./project_config.md#containerrepository-string).
This key value should contain the path
used to [tag](https://docs.docker.com/engine/reference/commandline/tag/) and push images to a new repository.

??? example

    ```json
    {
      "default_container_registry_path" : "harbor.my-organization.com/my-project/"
      ...
    }
    ```

`mp-build` constructs a tag using the **default_container_registry_path** and the lowercase value of the `adapter_kinds`
key in the `manifest.txt` file.
For example, if the adapter_kinds value is "AdapterName"
the resulting tag would be `harbor.my-organization.com/my-project/adaptername`.

## `container_port` (int, optional. default: 8080)

Specifies the port for the Adapter's REST server to bind on.
This value should only need to be changed if there is another process already using
port 8080. This will change the default for all projects. If you need to change the
port for an individual project, pass in the port using the `-P` (or `--port`) flag on
`mp-test` and `mp-build`.

??? example

    ```json
    {
        "container_port" : 8081,
        ...
     }
    ```

### `projects` (array of strings)

The SDK tools use this array of strings to track the locations of the projects.
Each string value is a project location, formatted as a **UNIX** or **DOS** path (host OS).
Tracking the location of each project allows
the SDK tools to be used anywhere in the console besides the project directory.
Any time a new project is created, tested, or built, the project is automatically appended to the list.
Projects that no longer exist in the specified location are automatically removed.

??? example

    ```json
    {
        "projects" : [
            "/user/management-paks/casandra-db-mp",
            "/user/management-paks/mysql-mp"
            ]
        ...
     }
    ```

