[![PyPI version](https://badge.fury.io/py/vmware-aria-operations-integration-sdk-lib.svg)](https://badge.fury.io/py/vmware-aria-operations-integration-sdk-lib)

Overview
--------
The VMware Aria Operations Integration SDK Library is a Python package that streamlines creating adapters using the
VMware Aria Operations Integration SDK.

Installing
---------
To install this package locally, run the following command:
```
pip install -i https://test.pypi.org/simple/ vmware-aria-operations-integration-sdk-lib
```

To install this package in an adapter container, add the following line to the `adapter_requirements.txt` file, 
substituting `x.y.z` for the desired version of the library.
```
vmware-aria-operations-integration-sdk-lib==x.y.z
```

Releasing
---------
https://packaging.python.org/en/latest/tutorials/packaging-projects/
1. Install dependencies:
   ```
   python3 -m pip install --upgrade build
   python3 -m pip install --upgrade twine
   ```
1. Increment the version in `setup.cfg`
1. Remove any previous distribution files:
   ```
   rm dist/*
   ```
1. Build the distribution files:
   python3 -m build
1. Upload to PyPi For testing:
   ```
   python3 -m twine upload --repository testpypi dist/*
   python3 -m pip install --index-url https://test.pypi.org/simple/ vmware-aria-operations-integration-sdk-lib-x.y.z --no-deps
   ```
   For distribution:
   ```
   python3 -m twine upload dist/*
   python3 -m pip install vmware-aria-operations-integration-sdk-lib-x.y.z
   ```
   In both cases, use `__token__` for the username, and paste the token (including `pypi-` prefix) as password

## Contributing

The vmware-aria-operations-integration-sdk project team welcomes contributions from the community. Before you start working
with vmware-aria-operations-integration-sdk, please read our [Developer Certificate of Origin](https://cla.vmware.com/dco).
All contributions to this repository must be signed as described on that page. Your signature certifies that you wrote
the patch or have the right to pass it on as an open-source patch. For more detailed information, refer
to [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the APACHE-2 License.
