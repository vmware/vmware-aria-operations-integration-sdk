Management Pack Build Tool
--------------------------

## Purpose

The mp-build tool builds a pak file and uploads the adapter container to a docker registry. `mp-build` does not perform
any tests on the adapter; to test the adapter code, use the [test tool](mp-test.md).

## Prerequisites
* The [vROps Integration SDK](../README.md#Installation) is installed, with the virtual environment active.
* A Management Pack project created by the [mp-init](mp-init.md) tool.
* Write permissions to a Docker registry that is accessible from vROps. The default registry/repository is the [TVS Harbor project](https://harbor-repo.vmware.com/harbor/projects/1067689/repositories) project. To ask for write permissions post a request in the [vrops-integration-sdk](https://vmware.slack.com/archives/C03KB8KF2VD) Slack channel.
## Input

### Command-line Arguments
```
-h, --help            show this help message and exit
-p PATH, --path PATH  Path to the project's root directory. Defaults to the current directory or prompts if the current directory is not a project.
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

#### Docker Registry Credentials
If the user is not logged into  [harbor-repo.vmware.com](harbor-reop.vmware.com) registry, `mp-build` will prompt
the user for their credentials. Credentials are lodged and stored using docker CLI:

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
The primary artifact of the `mp-build` tool is a pak file that can be uploaded directly to on-prem vROps installations. The vROps Integration SDK does not currently have support for vROps Cloud. 

The pak file contains: 
* The `manifest.txt` file and its localization inside the `resources` directory. 
* The EULA file(s)
* An optional Management Pack icon file
* All content inside the `content` directory.
* An adapter.zip file, containing:
  * The `conf` directory (including `describe.xml` and its localization file(s)).
  * A configuration file that includes information about the adapter, including the docker container's registry, repository, and digest. 

A pak file is a zip file created using the deflate compression algorithm. The contents can be inspected by using most unzip tools for extraction (depending on the tool, it may be necessary to rename the `.pak` extension to `.zip`).

### Logs
Logs from build process are written to the `logs/build.log` file. This is useful for debugging purposes in case the build fails.

## Troubleshooting
### Setting log level

Set log level to debug to see a verbose output of the program:
For Linux and macOS
```shell
LOG_LEVEL=debug mp-build
```
For Windows
```
set LOG_LEVEL=debug
mp-build
```
For Windows, set the log level back to `info` after debugging.

All logs can be seen in the command line, but they are also saved in  `logs/build.log` with `debug` log level.


### Docker Registry Permissions (Beta)
To acquire write permissions to [TVS Harbor Repository](https://harbor-repo.vmware.com/harbor/projects/1067689/repositories)
post a request to the [vrops-integration-sdk](https://vmware.slack.com/archives/C03KB8KF2VD) slack channel.

### Unexpected exception occurred while trying to build pak file (Beta)
While `mp-build` catches the most known exceptions, there is always the possibility of running into an unexpected error. 
Going through the debug logs might help expose the culprit. If the error isn't related to an individual configuration 
issue or isn't evident at first sight,isn't evident at first sight, contact [squirogacubi@vmware.com](mailto:squirogacubi@vmware.com) or [krokos@vmware.com](mailto:krokos@vmware.com) via email or Slack the [vrops-integrations-sdk](https://vmware.slack.com/archives/C03KB8KF2VD) channel.
 
