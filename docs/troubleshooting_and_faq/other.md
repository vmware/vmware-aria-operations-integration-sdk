# Other

### How can I implement Policy and Capacity models?

Policy and capacity models can only be specified by writing a `describe.xml` file in the `conf` directory.


### Are there replacements for  `onConfigure`, `onStopCollection`, and `onDiscard` methods?

The `onConfigure`, `onStopCollection`, and `onDiscard` methods have no replacement in the new integration SDK.


### VMware Aria Operations returns 'Unknown adapter type' when setting up new adapter instance

![Example of an 'Unknown Adapter Type' error message for an adapter with type/key 'Testserver'](../images/unknown_adapter_type.png)
> Example of an 'Unknown Adapter Type' error message for an adapter with type/key 'Testserver'.

If the pak file installs successfully but errors when creating an account (adapter instance), check that:

- The Collector/Group the MP is running on is a Cloud Proxy, and
- Check that the Cloud Proxy supports containerized adapters. Containerized adapter
  support is supported in VMware Aria Operations version 8.10.0 and later.

### Why am I seeing "Deleting connection-related elements from config.json" message?

As of version 1.0.0,
we've removed all connection-related elements from the [project config file](../references/project_config.md)
and migrated them to a new
[project connections JSON file](../references/project_connections_config.md)(`connections.json`).
As part of this change, both `mp-test` and `mp-build` will migrate the connection-related
elements to the `connections.json` file when present in the `config.json` file
(The new `connections.json` file is also added to the project's `.gitignore`
to prevent sensitive information from being committed).
Moving all the connection-related information away from the `config.json` file allows users
to include their project configuration file in version control,
making using the same `container_repository` for the project easier.

???+ note

    `mp-build` and `mp-init` do not remove `config.json` from `.gitignore`, so users who want to share the project's
    `config.json` file must remove it manually.
