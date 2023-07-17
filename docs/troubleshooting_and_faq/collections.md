# mp-test 


### `mp-test` returns '500 INTERNAL SERVER ERROR'

Internal server errors can happen for various reasons; however, the most common cause is an unhandled exception or syntax error in
the adapter's code. Check the server logs for clues about the issue. Sometimes, the problem may be detected using `mp-test` and
going over the terminal output.

### Collection returns 'No collection result was found'

`mp-test` runs a series of validations test after collection; if the collection has no results, then each validation step will report the result as missing.
When a collection result is missing, it usually means an error occurred during collection, but the Adapter handled the error. When the Adapter handles an error,
the response contains an error message; The console displays the error message. For example:

  ```python
  def collect(adapter_instance: AdapterInstance) -> CollectResult:
    result = CollectResult()
    try:
      raise Exception("oops")

      #...
    except Exception as e:
      logger.error("Unexpected collection error")
      logger.exception(e)
      result.with_error("Unexpected collection error: " + repr(e))
      return result
  ```

This code will output

  ```
  Building adapter [Finished]
  Waiting for adapter to start [Finished]
  Running Collect [Finished]
  Collection Failed: Unexpected collection error: Exception('oops')

  Avg CPU %                     | Avg Memory Usage %         | Memory Limit | Network I/O         | Block I/O
  ------------------------------+----------------------------+--------------+---------------------+--------------
  21.1 % (0.0% / 21.1% / 42.2%) | 4.0 % (4.0% / 4.0% / 4.0%) | 1.0 GiB      | 3.24 KiB / 6.67 KiB | 0.0 B / 0.0 B

  Collection completed in 0.45 seconds.

  No collection result was found.
  No collection result was found.
  All validation logs written to '/Users/user/management-pack/test-management-pack/logs/validation.log'
  ```
As seen above, the Exception is mentioned as the reason for the collection error, and the `No collection result was found` message is also shown.
Using the collection error message along with the `adapter.log` can help trace the cause of the issue.

### Is there a way to cache data for subsequent collections?

The containerized adapter does not support caching data between collections.

### Can I implement on-demand collections?

The containerized adapter does not support on-demand collections.

### Is there a way to cache data for subsequent collections?

The containerized adapter does not support caching data between collections.

### Can I implement on-demand collections?

The containerized adapter does not support on-demand collections.
