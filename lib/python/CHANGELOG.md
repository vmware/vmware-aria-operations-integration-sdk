VMware Aria Operations Integration SDK Library
----------------------------------------------
## 1.0.0 (10-23-2023)
* Release version 1.0.0 to coincide with version 1.1.0 of the SDK.
* Documentation fixes.

## 0.8.1 (09-15-2023)
* Improve error handling when log directory is not writable

## 0.8.0 (07-26-2023)
* Add py.typed files for typing support in compliance with PEP-561

## 0.7.3 (05-10-2023)
* Add labeled enum values support  
  
## 0.7.2 (04-18-2023)
* Add 'query_for_resources' method to SuiteApiClient
* Add helper function 'key_to_object' to suite_api_client
* Ensure 'Response' objects from SuiteApiClient are closed when used internally
* Add documentation about closing 'Response' objects from SuiteApiClient that are 
  returned to the calling code
* Improve Timer log messages 
* Fix issue where very small timespans would not show up in Timing Graph

## 0.7.1 (03-04-2023)
* Add 'Cores' and 'Millicores' to units.Misc (these are not convertible).

## 0.7.0 (03-04-2023)
* Fixes issue that prevented paged SuiteAPI requests from completing.
* Improves SuiteAPI logging and url handling.
* Adds an optional 'default_value' parameter to the Object::get_identifier method.
* Adds a 'Timer' class that automatically logs start and end times, and is able
  to generate an ascii chart of all times suitable for adapter logs.

## 0.6.0 (02-03-2023)
* If an AdapterDefinition is passed into a 'CollectResult', external object types
  are no longer returned in the result unless they contain content. Relationships
  are not affected. (Note: requires unreleased mp-test update).
* Adds 'RelationshipUpdateModes' enum to control how relationships are returned from 
  'CollectResult'.
* Add 'get_object' and 'get_objects_by_type' helper methods in 'CollectResult'.
* Add 'adapter_type()' and 'object_type()' helper methods in 'Object'.
* Add 'has_content()' method in 'Object' that returns true if the object contains 
  at least one metric, property, or event.
* Add 'collection_number' to Adapter Instance. Starts at 0 and increments each time 
  'collect' is called. Requires server based off of base-python-adapter 0.10.0 or 
  higher.
* Add 'collection_window' to Adapter Instance. Contains 'start_time' and 'end_time' 
  in ms since the Epoch. On the first collection, 'start_time' will be set to 0. 
  Requires server based off of base-python-adapter 0.10.0 or higher.

## 0.5.0 (01-25-2023)
* Add a 'adapter_logging' module simplify logging in adapters.
* Add python logging handler 'NullLogger' as the default logger, to suppress 
  messages if the calling adapter has not set up logging.

## 0.4.7 (01-13-2023)
* Fix a bug where the 'Authorization' header was set with an empty token when 
  acquiring a suite-api token, which in some cases resulted in 401 errors.

## 0.4.6 (12-9-2022)
* Fix a bug where default values for Events were not set correctly.

## 0.4.5 (11-17-2022)
* Add getters to Object class:
  - get_property_values
  - get_last_property_value
  - get_metric_values
  - get_last_metric_value
* Fix issue where auto-generated attribute timestamps only update once per collection.

## 0.4.4 (11-10-2022)
* Fix edge case when default value of an Integer Identifier is set to '0'.
* Fix case where adding automatically adding 'Content-Type' header in post requests caused an exception.

## 0.4.3 (11-03-2022)
* Fix case where 'None' was being coerced to a string.
* Set 'dashboard_order' default value to '0' instead of 'None'.
* Remove 'dt_type' from Metrics/Properties, as it is no longer used by Aria Ops.

## 0.4.2 (11-02-2022)
* Fix retrieval of SuiteAPI credentials.

## 0.4.1 (11-02-2022)
* Add paging to SuiteAPIClient.
* Rename VROpsSuiteApiClient to SuiteAPIClient.

## 0.4.0 (10-28-2022)
* Initial release with installation via PyPI.
