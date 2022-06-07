VIRTUAL_ENV_FILE_NAME="vrops_mp_sdk_venv"

DEPENDENCIES_MET=1

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
LT_BLUE='\033[1;34m'
DEFAULT='\033[0m'

function test_dependency() {
  NAME=${1}
  EXECUTABLE=${2}
  MIN_VERSION=${3}
  DOC_LINK=${4}

  echo -e "Checking ${NAME} version."

  if command -v "${EXECUTABLE}" >/dev/null 2>&1 ; then
    CUR_VERSION="$("${EXECUTABLE}" --version)"
    if [ "$(printf '%s\n' "$MIN_VERSION" "$CUR_VERSION" | sort -V | head -n1)" = "$MIN_VERSION" ]; then
      echo -e "${GREEN}${CUR_VERSION}${DEFAULT}"
    else
      echo -e "${RED}${CUR_VERSION}${DEFAULT}"
      echo -e "> ${YELLOW}Please update ${NAME} to ${MIN_VERSION} or later.${DEFAULT}"
      echo -e "> ${YELLOW}${NAME} downloads and installation instructions: ${DOC_LINK}${DEFAULT}"
      DEPENDENCIES_MET=0
    fi
  else
    echo -e "${RED}${NAME} is not installed${DEFAULT}"
    echo -e "> ${YELLOW}Please install ${NAME}.${DEFAULT}"
    echo -e "> ${YELLOW}${NAME} downloads and installation instructions: ${DOC_LINK}${DEFAULT}"
    DEPENDENCIES_MET=0
  fi

  echo -e ""
}

# Git is almost certainly installed if the user has gotten this far, but we'll test just in case they downloaded an
# archive instead of cloning the repo
test_dependency "Git" "git" "git version 2.35.0" "https://git-scm.com/downloads"
test_dependency "Python" "python3" "Python 3.3.0" "https://wiki.python.org/moin/BeginnersGuide/Download"
test_dependency "Docker" "docker" "Docker version 20.10.0" "https://docs.docker.com/engine/install/"

if [ $DEPENDENCIES_MET = 0 ] ; then
  echo -e "${RED}Please fix above dependency issues and rerun this install script${DEFAULT}"
  exit
fi

# Add path to repo
VROPS_SDK_REPO_PATH="$(realpath .)"
export VROPS_SDK_REPO_PATH

# Create virtual environment
(python3 -m venv $VIRTUAL_ENV_FILE_NAME)

# Activate virtual environment to source
source $VIRTUAL_ENV_FILE_NAME/bin/activate

## Install our package
pip install .

echo -e "${GREEN}Installation completed. Run the following command to activate the virtual environment:${DEFAULT}"
echo -e "${LT_BLUE}source $VIRTUAL_ENV_FILE_NAME/bin/activate${DEFAULT}"

