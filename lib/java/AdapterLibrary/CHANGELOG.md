VMware Cloud Foundation Operations Integration SDK Adapter Library for Java
---------------------------------------------------------------
## Unreleased

## 1.1.0 (02-07-2025)
* Add method for retrieving the x509 certificate from the CertificateInfo class.
* Fix the Timer class to ensure that it always stops even if the block it is timing throws an exception.
* Improve Documentation.

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
