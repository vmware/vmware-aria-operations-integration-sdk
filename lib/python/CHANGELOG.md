VMware Aria Operations Integration SDK Library
----------------------------------------------

## 0.4.5 (11-17-2022)
* Add getters to Object class:
  - get_property_values
  - get_last_property_value
  - get_metric_values
  - get_last_metric_value
* Fix issue where auto-generated attribute timestamps only update once per collection

## 0.4.4 (11-10-2022)
* Fix edge case when default value of an Integer Identifier is set to '0'
* Fix case where adding automatically adding 'Content-Type' header in post requests caused an exception

## 0.4.3 (11-03-2022)
* Fix case where 'None' was being coerced to a string
* Set 'dashboard_order' default value to '0' instead of 'None'
* Remove 'dt_type' from Metrics/Properties, as it is no longer used by Aria Ops

## 0.4.2 (11-02-2022)
* Fix retreival of SuiteAPI credentials

## 0.4.1 (11-02-2022)
* Add paging to SuiteAPIClient
* Rename VROpsSuiteApiClient to SuiteAPIClient

## 0.4.0 (10-28-2022)
* Initial release with installation via PyPI
