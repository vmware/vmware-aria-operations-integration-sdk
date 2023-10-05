### Adapter methods (required)

The methods in the adapter source code are required, and should be modified to generate a custom
adapter. Each method fulfills a request from the VMware Aria Operations collector, and can be tested individually using
`mp-test` (covered in [Testing a Management Pack](#testing-a-management-pack)).

- `test(adapter_instance)`:
  Performs a test connection using the information given to the adapter_instance to verify the adapter instance has been configured properly.
  A typical test connection will generally consist of:

    1. Read identifier values from adapter_instance that are required to connect to the target(s)
    2. Connect to the target(s), and retrieve some sample data
    3. If any of the above failed, return an error, otherwise pass.
    4. Disconnect cleanly from the target (ensure this happens even if an error occurs)

- `get_endpoints(adapter_instance)`:
  This method is run before the 'test' method, and VMware Aria Operations will use
  the results to extract a certificate from each URL. If the certificate is not trusted by
  the VMware Aria Operations Trust Store, the user will be prompted to either accept or reject
  the certificate. If it is accepted, the certificate will be added to the AdapterInstance
  object that is passed to the 'test' and 'collect' methods. Any certificate that is
  encountered in those methods should then be validated against the certificate(s)
  in the AdapterInstance. This method will only work against HTTPS endpoints, different types
  of endpoint will not work (e.g., database connections).

- `collect(adapter_instance)`:
  Performs a collection against the target host. A typical collection will generally consist of:
    1. Read identifier values from adapter_instance that are required to connect to the target(s)
    2. Connect to the target(s), and retrieve data
    3. Add the data into the CollectResult as objects, properties, metrics, etc
    4. Disconnect cleanly from the target (ensure this happens even if an error occurs)
    5. Return the CollectResult.

- `get_adapter_definition()`:
  Optional method that defines the Adapter Instance configuration. The Adapter Instance
  configuration is the set of parameters and credentials used to connect to the target and
  configure the adapter. It also defines the object types and attribute types present in a
  collection. Setting these helps VMware Aria Operations to validate, process, and display
  the data correctly. If this method is omitted, a `describe.xml` file should be manually
  created inside the `conf` directory with the same data. Generally, this is only necessary
  when using advanced features of the `describe.xml` file that are not present in this method.
 
!!! note

    The adapter is stateless. This means the adapter cannot store any data for use in later method calls.
