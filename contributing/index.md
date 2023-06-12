# SDK Structure

The SDK Git repository has the following layout:
* `.github/workflows`: Defines the GitHub Actions for the project: Deploying the [GitHub Pages](documentation.md) site, running [tests](tests.md)/CI, and formatting.
* `docs`: Sources for the [GitHub Pages](documentation.md) site.
* `images`: Contains all the container images used by adapters, and [tools for generating and publishing the images](docker.md).
* `images/base-python-adapter`: Sources for the base container image used by Python Adapters, including the [REST Server](http_server.md).
* `images/java-adapter`: Sources for the base container image used by Java Adapters. Extends the `base-python-adapter` image.
* `images/powershell-adapter`: Sources for the base container image used by Powershell Adapters. Extends the `base-python-adapter` image.
* `lib/python`: Sources for the Python Adapter Library (`vmware-aria-operations-integration-sdk-lib`).
* `samples`: Contains sample and template projects, for users to use, extend, or reference.
* `tests`: [Unit tests](tests.md) for the SDK tools.
* `vmware_aria_operations_integration_sdk`: Sources for the SDK tools (`mp-init`, `mp-test`, and `mp-build`).
