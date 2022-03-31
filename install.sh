VIRTUAL_ENV_FILE_NAME="vrops_mp_sdk_venv"

# Add path to repo
export VROPS_SDK_REPO_PATH="$(realpath .)"

# Create virtual environment
(python3 -m venv $VIRTUAL_ENV_FILE_NAME)


# Activate virtual environment to source
source $VIRTUAL_ENV_FILE_NAME/bin/activate

## Install our package
pip install .

echo "Installation completed. Run the following command to activate the virtual environment:"
echo "source $VIRTUAL_ENV_FILE_NAME/bin/activate"
