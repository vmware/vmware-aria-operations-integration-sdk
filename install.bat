:: maybe use setx instead
set VIRTUAL_ENV_FILE_NAME="vrops_mp_sdk_venv"

set "VROPS_SDK_REPO_PATH=%cd%"

:: Create virtual environment
python3 -m venv %VIRTUAL_ENV_FILE_NAME%

:: Activate virtual environment to source
call cd %VIRTUAL_ENV_FILE_NAME%/Scripts;activate.bat


:: TODO install prompt toolkit before running install
:: TODO run tool successfully
:: TODO install package in venv not local env
pip install .:: This install the package in the wrong place

echo "Everything went well"
