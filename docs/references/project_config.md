# Project Config File
* * *

The project config file is a JSON file called `config.json` located at the root of the project.
This document describes what data is present in the file.

## `default_memory_limit` (int, default: 1024)

Determines how much memory can be allocated to the container running the adapter. In
addition to the memory required by the Adapter, this includes memory used by the Base
OS layer and the Adapter's REST server. If this limit is exceeded, the container will
immediately exit.

## `container_repository` (string)

Specifies the container repository to be used by [mp-build](mp-build.md).
This key value should contain the  `host` and `path` used to
[tag](https://docs.docker.com/engine/reference/commandline/tag/) and push images to
the specified repository.

This overrides the [default_container_registry_path](global_config.md#defaultcontainerregistrypath-string-optional)
if it is present.

??? example

    ```json
    {
        "container_repository" : "harbor.my-organization.com/my-project/adaptername"
        ...
    }
    ```

## `container_push_repository` (string)

If this is present, this will override the `container_repository` value for the purposes
of pushing only. The value of `container_repository` will still be used by VMware Aria
Operations when pulling the adapter container image.
This key value should contain the  `host` and `path` used to
[tag](https://docs.docker.com/engine/reference/commandline/tag/) and push images to
the specified repository.

## `use_default_registry` (boolean)

If this is present and true (default is false), the registry portion of the 
`container_repository` will not be included with the management pack. This forces the end
user's default registry in VMware Aria Operations to be used instead. This is useful in
some distribution scenarios.