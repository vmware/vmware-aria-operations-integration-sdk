:: maybe use setx instead
set VIRTUAL_ENV_FILE_NAME="vrops_mp_sdk_venv"

set "VROPS_SDK_REPO_PATH=%cd%"

:: Create virtual environment
python3 -m venv %VIRTUAL_ENV_FILE_NAME%

:: Activate virtual environment to source
call cd %VIRTUAL_ENV_FILE_NAME%/Scripts;activate.bat


:: Install our package
pip install .

echo "Everything went well"
