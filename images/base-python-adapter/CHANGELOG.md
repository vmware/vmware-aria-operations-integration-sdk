VMware Aria Operations Integration Base Python Adapter

### 1.0.0 (10-20-2023)
* Release version 1.0.0 to coincide with version 1.1.0 of the SDK
* Modify the API contract to allow for null SuiteAPI credentials. This matches the actual behavior of the platform.

## 0.12.1 (09-15-2023)
* Improve logging setup error handling: Ensure that if the logs directory is not writable the Adapter
  will still run.
## 0.12.0 (05-03-2023)
* Add `schema_version` to adapter definition endpoint to track the schema version used by the Adapter
* Update Credential and Identifier enum type to support labels and display orders for each enum value
