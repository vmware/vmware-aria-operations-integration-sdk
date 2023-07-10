# Unit Tests

## Unit tests for the SDK Tools
SDK Unit Tests are located in the `tests` directory.
Tests are written for `pytest`, and can be manually started by running:
```shell
pytest -s tests
```
The SDK can run on Linux, macOS, and Windows, and as such the unit tests should
work on each of these operating systems.

There is a GitHub Action (`.github/workflows/aria-operations-integration-sdk.yaml`) 
that runs these tests for each OS and each supported Python version on each Pull 
Request.

## Unit tests for the Python Adapter Library
Python Adapter Library Unit Tests are located in the `lib/python/tests` directory.
Tests are written for `pytest`, and can be manually started by running:
```shell
pytest -s lib/python/tests
```
The Python Adapter Library is designed to run on the base container image which is 
based on Debian Linux. As such, the tests are only run on a Linux environment

There is a GitHub Action (`.github/workflows/aria-operations-integration-sdk.yaml`)
that runs these tests for Linux with each supported Python version on each Pull
Request.



