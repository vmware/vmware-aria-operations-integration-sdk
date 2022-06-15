Management Pack Initialization Tool
-----------------------------------

## Purpose

The mp-build tool builds a pak file and uploads the adapter container to a docker registry. `mp-build` does not perform
any tests on the adapter; to test the adapter code, use the [test tool](mp-test.md).

## Prerequisites
### vROps Implementation SDK:
Most prerequisites for the `mp-build` tool, including the tool itself, are installed during the installation of vROps
implementation SDK. To install the vROps implementation SDK, consult the [installation](../README.md#installation) section of the README.

### Write permissions to the TVS Harbor project:
The `mp-build` tool uses harbor to store the image related to the [Dockefile](mp-init#Dockerfile), so the user is required to have  
write permissions to the [TVS Harbor project](https://harbor-repo.vmware.com/harbor/projects/1067689/repositories) project.
To obtain write permissions, post a request in the [vrops-integrations-sdk](https://vmware.slack.com/archives/C03KB8KF2VD) slack channel.

## Input

### Command-line Arguments
```shell
-h, --help            show this help message and exit
-p PATH, --path PATH  Path to the project's root directory. Defaults to the current directory or prompts if the current directory is not a project.
```

### Interactive Prompts
When using the `mp-build` script, if the user isn't standing in a directory with a project, the user will be prompt to select
a project to build:

```shell
Select a project:
 ❯ /Users/user/projects/test
   /Users/user/projects/nsx-alb-avi
   Other
```

If the user is not logged into  [harbor-repo.vmware.com](harbor-reop.vmware.com) registry, `mp-build` will prompt
the user for their credentials. Credentials are lodged and stored using docker CLI:

```shell
Login into harbor-repo.vmware.com
Username: user 
Password:  
Login Succeeded
```

##  Output
After logging into harbor, `mp-build` will upload the image related to the Dockerfile located at the project's root.
Then, it will generate a pak file inside the project's build directory. The Management paks name comes from the adapter
key provided during the `mp-build` process and the adapter version; both fields are inside the `manifest.txt` file under
the keys `name` and `version`.

```shell
build
└── ManagemenPack_1.0.0.pak
```
The pak file produced by `mp-build` contains a copy of the manifest.txt  along with all content
While the main output of `mp-build` is a pak file that is ready to be uploaded to vROps, it also outputs a log file
`log/build.log` can be used for debugging purposes in case the build fails.

## Troubleshooting
### Setting log level

Set log level to debug to see a verbose output of the program:
For Linux and Mac Os
```shell
LOG_LEVEL=debug mp-build
```
For Windows
```
set LOG_LEVEL=debug
mp-build
```
For Windows, set the log level back to `info` after debugging.

All logs can be seen in the command line, but they are also saved in a  `logs/build.log` with `debug` log level.


### Docker Registry Permissions (Beta)
To acquire write permissions to [TVS Harbor Repository](https://harbor-repo.vmware.com/harbor/projects/1067689/repositories)
contact squirogacubi@vmware.com or krokos@vmware.com  via email or Slack private message.

### Unexpected exception occurred while trying to build pak file (Beta)
While `mp-build` catches the most known exceptions, there is always the possibility of running into an unexpected error. Going through the debug logs might help expose the culprit. If the error isn't related to an individual configuration issue or
isn't evident at first sight, post your issue in the [vrops-integration-sdk](https://vmware.slack.com/archives/C03KB8KF2VD) slack channel. 
