
**`default_container_registry_path`** (string, optional): Specifies the default container registry path to be used by [mp-build](mp-build.md) any time the local **config.json** file doesn't contain a container registry. This key value should contain the path used to [tag](https://docs.docker.com/engine/reference/commandline/tag/) and push images to a new repository. For example: 
 ``` json
{
    "default_container_registry_path" : "projects.registry.vmware.com/vmware_aria_operations_integration_sdk/"
    ...
 }
 ```

Will by used by `mp-build` to construct a tag using the **default_container_registry_path** and the lowercase value  of the `adapter_kinds` key  in the manifest.txt file. If the adapter_kinds value is "AdapterName" the resulting tag would be `projects.registry.vmware.com/vmware_aria_operations_integration_sdk/adaptername`.


**`projects`** (array of strings): This array of strings is used by the SDK tools to track the locations of the projects. Each string value is a project location, formatted as a **UNIX** or **DOS** path (host OS). Tracking the location of each project allows the SDK tools be used anywhere in the console besides the project directory. Every time a project is created using [mp-test](mp-test.md) or built from the root directory of the project using `mp-build`, they are automatically appended to the list.

 ``` json
{
    "projects" : [
        "/user/management-paks/casandra-db-mp",
        "/user/management-paks/mysql-mp"
        ]
    ...
 }
 ```
