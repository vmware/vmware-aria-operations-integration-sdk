
Installing
---------
To install this package, run the following command while standing in the python directory 
```
pip install -i https://test.pypi.org/simple/ vrops-integration
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
1. Upload to PyPi
   For testing:
   ```
   python3 -m twine upload --repository testpypi dist/*
   python3 -m pip install --index-url https://test.pypi.org/simple/ vrops-integration-x.y.z --no-deps
   ```
   For distribution:
   ```
   python3 -m twine upload dist/*
   python3 -m pip install vrops-integration-x.y.z
   ```
   In both cases, use `__token__` for the username, and paste the token (including `pypi-` prefix) as password

