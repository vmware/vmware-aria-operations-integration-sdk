VMware Aria Operations Integration SDK Adapter Library for Java
---------------------------------------------------------------
## 1.0.3 (03-12-2024)
* Fix deserialization error when reading in certificate data.

## 1.0.2 (11-15-2023)
* Fix deserialization error when reading in a password field on a credential.
* Prevent extraneous 'type' attributes from appearing in String Property and Numeric Property Json Objects.
* Add 'queryForResources' method in SuiteApiClient.

## 1.0.1
* Prevent `JsonDecodingException` in calls to `AdapterInstance` constructor when no SuiteAPI credentials are present.
* Prevent `NoSuchElementException` in calls to `Timing.graph()` when no timers are present.

## 1.0.0 
* Initial release.
