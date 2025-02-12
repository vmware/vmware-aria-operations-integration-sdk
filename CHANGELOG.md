VMware Aria Operations Integration SDK
--------------------------------------
## 1.2.0 (02-12-2025)
* Fix and updates to Adapter Libraries
* `config.json` will let you specify a different push repository from the pull repository by using the `container_push_repository` property.
 ```json
  {
      [...],
      "container_repository": "pull_images_from_this_repository.repository.com/images/test_mp",
      "container_push_repository": "push_images_to_this_repositroy.repository.com/images/test_mp"
  }
  ```
* Also in `config.json`, there is a `use_default_registry` key that takes a boolean. The default is null/false, but if set to true the registry that the image is pushed to will be omitted from the pack file.
* Instances of projects.registry.vmware.com have been replaced by projects.packages.broadcom.com
* The Python Adapter Library has been bumped to 1.1.0.
* The Java Adapter Library has been bumped to 1.1.0.
* When generating a new project, the ‘images’ directory (containing icons for object kinds, adapter kinds, and traversals), is now in the correct location.
* When generating a new Java project, it now defaults to the latest version of the Java Adapter Library, which addresses issues where things didn’t work out of the box.
* A number of dependencies have been updated to address security vulnerabilities.

## 1.1.0 (10-23-2023)
* Add Java support
* Improve logging when building a container image fails
* Fix a dependency issue with xmlschema
* Fix issue where Suite API connection information in `connections.json` did not inherit
  default values correctly
* Fix issue where SuiteAPI behavior in an `mp-test` Test Connection did not match the
  behavior in VMware Aria Operations during Test Connection and Get Endpoints. Specifically, 
  on the platform the SuiteAPI credentials are only sent during a Collection, as that is the
  only time the SuiteAPI is intended to be used. However, `mp-test` had been sending SuiteAPI 
  credentials for all three operations. The behavior of `mp-test` now matches the platform.


## 1.0.1 (09-15-2023)
* Update dependencies to resolve a security vulnerability in GitPython
* Fix issue where registry URL would not parse correctly if a port was not present
* Fix issue where server would repeatedly crash if logging directory was not writable
  * If user runs mp-init using root, the logs directory's permissions are set to world-wriable
  * If user runs mp-init as root, mp-init warns that the above will happen
  * Improves error handling when logs directory is not writable to prevent server crashes

## 1.0.0 (07/26/2023)
* Improve documentation site
* Additional sample and template projects
* Connections in the 'config.json' file are now in their own 'connections.json' file
* 'mp-build' no longer hangs when at startup when a virtual environment is present
* Adapter directories no longer have a 'adapter3' suffix
* Improved registry handling, especially when using DockerHub
* Option to create a new project with a template that does not include sample code

## 0.5.1 (05-10-2023) 
* Update docker module version to fix urllib3 2.0.0 incompatibility.
* Update adapter template with current best practices.
* mp-init now generates icon folders for AdapterKind, ResourceKind, and TraversalSpec.
* Add labeled enum values support (requires SDK library 0.7.3).

## 0.5.0 (04-20-2023)
* Default container registry can now be specified in global config file
* Fix issue where psutil version would cause python build to fail
* Standardize encoding of properties file to 'utf-8'
* Add two flags to mp-test for controlling collection parameters:
  * '--collection-number': Sets the collection number. This is useful for testing functionality that only occurs on some collection cycles.
  * '--collection-window-duration': Sets the duration of the collection window. This is useful for testing how the adapter behaves for longer or shorter collection windows.
  These flags require a server version of 0.11.0 or later.
* Improve visibility of failed test connections.
* Add record of successfull validation tests to 'validation.log'
* Improve container image build times.
* Fix an issue that in certain scenarios would result in a pak file failing to install.
* Implement log rotation for 'test.log' and 'build.log' files.
* Add explanation of cell format to statistics output in mp-test.
* Add '--version' flag to 'mp-init', 'mp-test', and 'mp-build' that returns the current SDK version.
* Do not include '.gitkeep' files in pak files.
* Add several flags to mp-build for running on headless build servers:
  * '--no-ttl': Remove UI flourishes and prompts that require a TTL.
  * '--registry-tag': Specify the container registry to upload the built adapter container to without relying on the 'config.json' file.
  * '--registry-username': Specify the registry username if docker is not logged in to the registry.
  * '--registry-password': Specify the registry password if docker is not logged in to the registry.
* Improve logging in adapter created from 'mp-init'.
* Fix issue that was preventing installation on Windows.
* 'mp-test' asks for SuiteAPI credentials when setting up a new connection.
* 'Long collection' tests now automatically detect several common issues.

## 0.4.0 (11-16-2022)
* Initial release with installation via PyPI
