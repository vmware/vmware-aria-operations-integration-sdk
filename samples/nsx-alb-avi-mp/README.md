# NSX ALB Sample MP

## Requirements
- [Integration SDK](../../docs/get_started.md#requirements)
- An accessible NSX ALB instance with valid API credentials
 
## About the MP

This Management Pack collects several object types from an NSX ALB environment, with some
basic properties and metrics. It can be used as-is, as a reference, or as a starting point
for creating a custom management pack.

## Building
### Build pak file
- Run `mp-build` at the root of the sample project directory. `mp-build` uses the given container registry to 
  upload a container image that contains the adapter. The cloud proxy pulls the container image from the registry and
  runs the adapter inside the container. Consult the [Troubleshooting](../../docs/troubleshooting_and_faq.md) section for 
  additional information about setting up container registries.

