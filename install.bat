:: maybe use setx instead
set VIRTUAL_ENV_FILE_NAME=vrops_mp_sdk_venv

set "VROPS_SDK_REPO_PATH=%cd%"

:: Create virtual environment
echo "Creating python virtual environament"
python -m venv %VIRTUAL_ENV_FILE_NAME%

echo "Installing Python dependencies and tooling in virtual environament"
:: Activate virtual environment to source
call .\%VIRTUAL_ENV_FILE_NAME%\Scripts\activate.bat; pip install .

echo "Run activate.bat script located at %VROPS_SDK_REPO_PATH%/Scripts/activate.bat"

