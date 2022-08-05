Management Pack Test Tool
-------------------------

## Purpose

The `mp-test` tool is used to test an adapter locally. It can verify that each of the `collect`, `test connection`, `endpoint urls`, and `version` endpoints run, validates that the output conforms to the vROps API, and displays the output along with any errors that were found.

If the test tool runs error-free on each endpoint, then the Management Pack should run successfully on vROps.

## Prerequisites

* The [vROps Integration SDK](../README.md#Installation) is installed, with the virtual environment active.
* A Management Pack project created by the [mp-init](mp-init.md) tool.

## Input

### Command-line Arguments
```
usage: mp-test [-h] [-p PATH] [-c CONNECTION] [-v {0,1,2,3}]
               {connect,collect,long-run,endpoint_urls,version,wait} ...

Tool for running adapter test and collect methods outside of a vROps Cloud Proxy.

positional arguments:
  {connect,collect,long-run,endpoint_urls,version,wait}
    connect             Simulate the 'test connection' method being called by the vROps collector.
    collect             Simulate the 'collect' method being called by the vROps collector.
    long-run            Simulate a long run collection and return data statistics about the overall collection.
    endpoint_urls       Simulate the 'endpoint_urls' method being called by the vROps collector.
    version             Simulate the 'version' method being called by the vROps collector.
    wait                Simulate the adapter running on a vROps collector and wait for user input to stop.
                        Useful for calling REST methods via an external tool, such as Insomnia or Postman.

optional arguments:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  Path to root directory of project. Defaults to the current directory, or prompts if
                        current directory is not a project.
  -c CONNECTION, --connection CONNECTION
                        Name of a connection in this project.
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Determine the amount of console logging when performing validation. 0: No console
                        logging; 3: Max console logging.
```

In addition, when using `collect` and `long-run` there are additional optional arguments:

`mp-test collect`
```
usage: mp_test.py collect [-h] [-n TIMES] [-w WAIT]

optional arguments:
  -h, --help            show this help message and exit
  -n TIMES, --times TIMES
                        Run the given method 'n' times.
  -w WAIT, --wait WAIT  Amount of time to wait between collections (in seconds).
```

`mp-test long-run`

```
usage: mp-test long-run [-h] [-d DURATION] [-i COLLECTION_INTERVAL]

optional arguments:
  -h, --help            show this help message and exit
  -d DURATION, --duration DURATION
                        Duration of the long run in h hours, m minutes, or s seconds. 
  -i COLLECTION_INTERVAL, --collection-interval COLLECTION_INTERVAL
                        Amount of time to wait between collections.

```
### Interactive Prompts

#### Project
In order to test an adapter, the tool needs to know which adapter to test. This is done by specifying the project. It can be set in a number of ways. 
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

#### Connection
A connection provides the inputs the adapter needs to connect to the target it will monitor, similar to creating a new Account (Adapter Instance) in vROps. A connection is derived from the `conf/describe.xml` file, and includes configuration fields and a credential (if one exists). See [Adding a Configuration Field to an Adapter](adding_to_an_adapter.md#Adding a Configuration Field to an Adapter Instance) and [Adding a Credential](adding_to_an_adapter.md#Adding a Credential). Connections are specific to each Management Pack. The connection must be specified, and can be set in a number of ways.
* If the `-c CONNECTION_NAME` or `--connection CONNECTION_NAME` argument is specified, the connection with the given name will be used. 
* If a command line argument was not provided, or it was not a valid connection name, the tool will prompt the user to select an existing connection or create one:
    ```
    Choose a connection:
    ❯ database1
      database1_bad_credentials
      New Connection
    ```
    If `New Connection` is selected, than the test tool will prompt for a value for each configuration field (Resource Identifier) in the adapter instance resource of the describe.xml file. If the adapter instance resource has a credential, the tool will also prompt for each of the fields in the credential.
 
    For example, in the default template there is no credential and a single configuration field called 'ID', so when creating a New Connection, the tool will prompt for a single field called 'ID':
    ```
    Enter connection parameter 'ID': 
    ```
    
    > Note: If a credential field is set as a password, the prompt will be obscured, however **it will be stored as plaintext in the project configuration file**.

    Finally, after all configuration and credential fields have been entered, the tool will prompt for a name for the connection. This is used to identify the connection in either a command line argument or in the interactive prompt.
    ```
    Enter a name for this connection:
    ```
#### Method
Adapters must implement four endpoints: `Test Connection`, `Collect`, `Endpoint URLs`, and `Version`. Each invocation of the test tool can test one of these methods. The method must be specified, and can be set in a number of ways.
* If one of the positional command line arguments was specified (`connect`, `collect`, `long-run`, `endpoint_urls`, `version`, or `wait`), that method will be used. 
* If no command line argument for the method was provided, the tool will prompt the user to select one:
    ```
    Choose a method to test:
     ❯ Test Connection
       Collect
       Long Run Collection
       Endpoint URLs
       Version
    ```
## Output

The output of the test tool consists of three parts.
### Result

The result is simply a JSON representation of the return value of the method that was called that is written to the console. For example, for the `collect` method, the result will have objects, metrics, properties, events, and relationships that are collected by the adapter code. The result should be manually inspected to ensure that all objects, relationships, etc are present as intended.

### Validation
After the result is received, the tool does some automatic validation of the results. If any issues are detected, the tool will write `Validation Failed:` to the console below the JSON result, followed by a list of the errors.
The tool performs the following validation:
* Ensure that the result JSON conforms to
  the [vROps Collector API Spec](../vrealize_operations_integration_sdk/api/vrops-collector-fwk2-openapi.json)
  .

### Logs
Logs from the server (`server.log`) and adapter (by default, `adapter.log`, but this can be changed) are written to the `logs` directory. This is useful for debugging issues or exceptions during execution.

## Troubleshooting
### Setting log level

Set log level to debug to see a verbose output of the program:
For Linux and macOS
```shell
LOG_LEVEL=debug mp-test
```
For Windows
```
set LOG_LEVEL=debug
mp-test
```
For Windows, set the log level back to `info` after debugging.

All logs can be seen in the command line, but they are also saved in `logs/test.log` with `debug` log level.

### Unexpected exception occurred while trying to build pak file (Beta)
While `mp-test` catches the most known exceptions, there is always the possibility of running into an unexpected error. Going through the debug logs might help expose the culprit. If the error isn't related to an individual configuration issue, or
isn't evident at first sight, contact [squirogacubi@vmware.com](mailto:squirogacubi@vmware.com) or [krokos@vmware.com](mailto:krokos@vmware.com) via email or Slack the [vrops-integrations-sdk](https://vmware.slack.com/archives/C03KB8KF2VD) channel.
