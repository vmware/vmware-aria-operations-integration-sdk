VMware Aria Operations Integration SDK
--------------------------------------
## Unreleased
* Improves visibility of failed test connections.
* Adds record of successfull validation tests to 'validation.log'
* Improves container image build times.
* Fixes an issue that in certain scenarios would result in a pak file failing to install.
* Implements log rotation for 'test.log' and 'build.log' files.
* Add explanation of cell format to statistics output in mp-test.
* Adds '--version' flag to 'mp-init', 'mp-test', and 'mp-build' that returns the current SDK version.
* Do not include '.gitkeep' files in pak files.
* Adds several flags to mp-build for running on headless build servers:
  * '--no-ttl': Remove UI flourishes and prompts that require a TTL.
  * '--registry-tag': Specify the container registry to upload the built adapter container to without relying on the 'config.json' file.
  * '--registry-username': Specify the registry username if docker is not logged in to the registry.
  * '--registry-password': Specify the registry password if docker is not logged in to the registry.
* Improve logging in adapter created from 'mp-init'.
* Fixes issue that was preventing installation on Windows.
* 'mp-test' asks for SuiteAPI credentials when setting up a new connection.
* 'Long collection' tests now automatically detect several common issues.

## 0.4.0 (11-16-2022)
* Initial release with installation via PyPI
