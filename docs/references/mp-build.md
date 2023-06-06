# mp-build
--------------------------

## Purpose

The mp-build tool builds a pak file and uploads the adapter container to a registry. `mp-build` does not perform
any tests on the adapter; to test the adapter code, use the [test tool](mp-test.md).

## Prerequisites
* The [VMware Aria Operations Integration SDK](../index.md#installation) is installed, with the virtual environment active.
* A Management Pack project created by the [mp-init](mp-init.md) tool.
* Write permissions to a container registry that is accessible from VMware Aria Operations.
 
## Input

### Command-line Arguments
```
  -h, --help            show this help message and exit
  -p PATH, --path PATH  Path to root directory of project. Defaults to the current directory, or prompts if current directory is not a project.
  -r [REGISTRY_TAG], --registry-tag [REGISTRY_TAG]
                        The full container registry tag where the container image will be stored (overwrites config file).
  --registry-username REGISTRY_USERNAME
                        The container registry username.
  --registry-password REGISTRY_PASSWORD
                        The container registry password.
  -i, --insecure-collector-communication
                        If this flag is present, communication between the collector (Cloud Proxy) and the adapter will be unencrypted. If using a custom server with this option, the server must
                        be configured to listen on port 8080.
```

### Interactive Prompts
#### Project
In order to build an adapter, the tool needs to know which adapter to build. This is done by specifying the project. It can be set in a number of ways. 
 
* If the `-p PROJECT_PATH` or `--path PROJECT_PATH` argument is specified, the project in the path will be used.
 
* If the current working directory is a Management Pack project, that project will be used (unless a valid project was specified in command line arguments).
 
* If neither of the above options resolves to a valid project, the tool will prompt the user to select one:
 
    ```
     Select a project:
     ❯ /Users/user/projects/test
       /Users/user/projects/nsx-alb-avi
       Other
     ```
 
If 'Other' is selected, the tool will prompt for a project path. If the path is a valid project, the path will be saved and appear in the project selection prompt in the future.

#### Registry Credentials
If the user is not logged into a container registry, `mp-build` will prompt
the user to sign in to one and enter their credentials. By default `mp-build` uses the 'default_container_registry' specified in the [global config file](global_config.md). Alternatively, the user can use
the `--registry-tag`, `--registry-username`,`--registry-password`. Passing `--registry-tag` without specifying a registry will use the registry specified in 
the local config.json file. If no registry exists in the config.json file, the user will be prompted to enter a one. Credentials are logged and stored using docker CLI:

```shell
Login into harbor-repo.vmware.com
Username: user 
Password:  
Login Succeeded
```

##  Output
After logging into harbor, `mp-build` will upload the image related to the Dockerfile located in the project's root directory.
Then, it will generate a pak file inside the project's build directory. The Management Pack's name comes from the adapter
key (provided during the `mp-init` process) and the adapter version. Both fields are in the `manifest.txt` file under
the keys `name` and `version`.

```shell
build
└── ManagementPack_1.0.0.pak
```
### Pak file
The primary artifact of the `mp-build` tool is a pak file that can be uploaded directly to on-prem VMware Aria Operations installations. The VMware Aria Operations Integration SDK does not currently have support for VMware Aria Operations Cloud. 

The pak file contains: 
* The `manifest.txt` file and its localization inside the `resources` directory. 
* The EULA file(s)
* An optional Management Pack icon file.
* All content inside the `content` directory.
* An adapter.zip file, containing:
  * The `conf` directory (including `describe.xml` and its localization file(s)).
  * A configuration file that includes information about the adapter, including the container's registry, repository, and digest. 

A pak file is a zip file created using the deflate compression algorithm. The contents can be inspected by using most unzip tools for extraction (depending on the tool, it may be necessary to rename the `.pak` extension to `.zip`).

### Logs
Logs from build process are written to the `logs/build.log` file. This is useful for debugging purposes in case the build fails.
