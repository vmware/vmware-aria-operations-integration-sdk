# mp-test

### `mp-test` hangs on 'Building Adapter'

If this is the first time testing an Adapter, most likely the build process is active but taking a long time to complete.
There are several sub-steps that are performed:

* Downloads the base image(s)
* Download and install any dependencies
* Compiles the Adapter code (if required by the language)
* Assembles the resulting container

Depending on the size of the base image(s), and the download speed of your internet 
connection, it can take some time build the Adapter image the first time.
Subsequent builds should be much faster as the intermediate steps are cached. 
See below for approximate image sizes.

| Language | Stage       | Image                     | Compressed Size |
|----------|-------------|---------------------------|-----------------|
| Python   | Compilation | N/A                       | N/A             |
| Python   | Execution   | base-adapter:python-1.0.0 | 54 MiB          |
| Java     | Compilation | gradle:8.3.0-jdk17        | 341 MiB         |
| Java     | Execution   | base-adapter:java-1.0.0   | 212 MiB         |

### `mp-test` returns '500 INTERNAL SERVER ERROR'

Internal server errors can happen for various reasons; however, the most common cause is an unhandled exception or syntax error in
the adapter's code. Check the server logs for clues about the issue. Sometimes, the problem may be detected using `mp-test` and
going over the terminal output.

---
### Collection returns 'No collection result was found'

`mp-test` runs a series of validations test after a collection; if the collection has no results, then each validation
step will report the result as missing.
When a collection result is missing, it usually means an error occurred during a collection,
but the Adapter handled the error.
When the Adapter handles an error, the response contains an error message; The console displays the error message.
For example:

=== "Python Adapter Library"

      ```python linenums="1"
      def collect(adapter_instance: AdapterInstance) -> CollectResult:
        result = CollectResult()
        try:
          raise Exception("oops!")

          #...
        except Exception as e:
          logger.error("Unexpected collection error")
          logger.exception(e)
          result.with_error(f"Unexpected collection error: '{e}'")
          return result
      ```

=== "Java Adapter Library"

      ```python linenums="1"
      public CollectRestuls collect(AdapterInstance adapterInstance) {
        CollectResult result = new CollectResult();
        try{
          throw new Exception("oops!");

          //...
        } catch ( Exception  e) {
          result.with_error("Unexpected collection error: " + "'" + e.getMessage() + "'");
        }

        return result
      }
      ```

will output

  ``` hl_lines="4"
  Building adapter [Finished]
  Waiting for adapter to start [Finished]
  Running Collect [Finished]
  Collection Failed: Unexpected collection error: 'oops!'

  Avg CPU %                     | Avg Memory Usage %         | Memory Limit | Network I/O         | Block I/O
  ------------------------------+----------------------------+--------------+---------------------+--------------
  21.1 % (0.0% / 21.1% / 42.2%) | 4.0 % (4.0% / 4.0% / 4.0%) | 1.0 GiB      | 3.24 KiB / 6.67 KiB | 0.0 B / 0.0 B

  Collection completed in 0.45 seconds.

  No collection result was found.
  No collection result was found.
  All validation logs written to '/Users/user/management-pack/test-management-pack/logs/validation.log'
  ```

As seen above, the Exception is mentioned as the reason for the collection error, and
the `No collection result was found` message is also shown.
Using the collection error message along with the `adapter.log` can help trace the cause of the issue.

---
### How do I migrate connection-related elements from config.json to connections.json?

As of version 1.0.0,
all connection-related elements from the [project config file](../references/project_config.md)
have been migrated to a new
[project connections JSON file](../references/project_connections_config.md)(`connections.json`).
As part of this change, both `mp-test` and `mp-build` will offer to migrate connection-related
elements to the `connections.json` file when present in the `config.json` file
(The new `connections.json` file is automatically added to the project's `.gitignore`
to prevent sensitive information from being committed).
Moving all the connection-related information away from the `config.json` file allows users
to include their project configuration file in version control,
making using the same `container_repository` for the project easier.

???+ note

    - `mp-build` and `mp-init` do not remove `config.json` from `.gitignore`, so users who want to share the project's
    `config.json` file must remove it manually.
    - If `connections.json` exists, the user will not be prompted.

---
???+ info

    For additional issues regarding mp-test and docker, see the [Docker](docker.md) page.
