# Adapter Design

### Are there replacements for `onConfigure`, `onStopCollection`, and `onDiscard` methods?

The `onConfigure`, `onStopCollection`, and `onDiscard` methods from the traditional Java SDK have no replacement in the Integration SDK.

---
### Can an Adapter collect for multiple Accounts/Adapter Instances?

The methods in an Adapter (collect, test, etc.) are called with a single Adapter Instance. 
If multiple Accounts in the Aria Operations UI are created, each Account will have a corresponding 
instance of the Adapter running as a container to handle its requests. Thus, if you create two 
Accounts, the `collect` method will be called twice (in isolated containers) every collection cycle - once per 
Account/Adapter Instance. 

---
### Can I implement on-demand collections?

Adapters do not support on-demand collections.

---
### Is there a way to cache data for subsequent collections?

Adapters do not support caching data between collections.

---
### Can I add two credentials to an Account/Adapter Instance?

No. Each Account/Adapter Instance can only have a single credential. If you _need_ multiple sets of credentials for a single
collection, for example to merge data from two different types of endpoints, you could make a single credential that has four fields: 
`endpoint1_username`, `endpoint1_password`, `endpoint2_username`, `endpoint2_password`.
Generally, however, one Account/Adapter Instance per endpoint is recommended.

---
### Can I implement Policy and Capacity models?

Policy and capacity models can only be specified by writing a `describe.xml` file in the `conf` directory.
These models are not yet documented outside of the `describe.xsd` file.

