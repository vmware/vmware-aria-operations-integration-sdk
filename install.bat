set VIRTUAL_ENV_FILE_NAME=vrops_mp_sdk_venv

set "VROPS_SDK_REPO_PATH=%cd%"

:: Create virtual environment
echo "Creating python virtual environment"
python -m venv %VIRTUAL_ENV_FILE_NAME%

echo "Installing Python dependencies and tooling in virtual environment"
:: Activate virtual environment to source
call .\%VIRTUAL_ENV_FILE_NAME%\Scripts\activate.bat
call pip install .

:: Deactivate virtual environment, so the user experience is the same for both platforms
call deactivate
echo "Installation completed. Run the following command to activate the virtual environment: source <VIRTUAL_ENV_FILE_NAME>/bin/activate"
