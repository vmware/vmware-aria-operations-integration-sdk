VIRTUAL_ENV_FILE_NAME="vrops_mp_sdk_venv"

DEPENDENCIES_MET=1

RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
BLUE=$(tput setaf 4)
MAGENTA=$(tput setaf 5)
CYAN=$(tput setaf 6)
WHITE=$(tput setaf 7)
LT_BLUE=$(tput setaf 153)
BRIGHT=$(tput bold)
DEFAULT=$(tput sgr0)

function test_dependency() {
  NAME=${1}
  EXECUTABLE=${2}
  MIN_VERSION=${3}
  DOC_LINK=${4}

  printf "Checking %s version.\n" "$NAME"

  if command -v "${EXECUTABLE}" >/dev/null 2>&1 ; then
    CUR_VERSION="$("${EXECUTABLE}" --version)"
    if [ "$(printf '%s\n' "$MIN_VERSION" "$CUR_VERSION" | sort -V | head -n1)" = "$MIN_VERSION" ]; then
      printf "%s%s%s\n" "$GREEN" "$CUR_VERSION" "$DEFAULT"
    else
      printf "%s%s%s\n" "$RED" "$CUR_VERSION" "$DEFAULT"
      printf "> %sPlease update %s to %s or later.%s\n" "$YELLOW" "$NAME" "$MIN_VERSION" "$DEFAULT"
      printf "> %s%s downloads and installation instructions: %s%s\n" "$YELLOW" "$NAME" "$DOC_LINK" "$DEFAULT"
      DEPENDENCIES_MET=0
    fi
  else
    printf "%s%s is not installed%s\n" "$RED" "$NAME" "$DEFAULT"
    printf "> %sPlease install %s.%s\n" "$YELLOW" "$NAME" "$DEFAULT"
    printf "> %s%s downloads and installation instructions: %s%s\n" "$YELLOW" "$NAME" "$DOC_LINK" "$DEFAULT"
    DEPENDENCIES_MET=0
  fi

  printf "\n"
}

# Git is almost certainly installed if the user has gotten this far, but we'll test just in case they downloaded an
# archive instead of cloning the repo
test_dependency "Git" "git" "git version 2.35.0" "https://git-scm.com/downloads"
test_dependency "Python" "python3" "Python 3.3.0" "https://wiki.python.org/moin/BeginnersGuide/Download"
test_dependency "Docker" "docker" "Docker version 20.10.0" "https://docs.docker.com/engine/install/"

if [ $DEPENDENCIES_MET = 0 ] ; then
  printf "%sPlease fix above dependency issues and rerun this install script%s\n" "$RED" "$DEFAULT"
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

printf "%sInstallation completed. Run the following command to activate the virtual environment:%s\n" "$GREEN" "$DEFAULT"
printf "%ssource %s/bin/activate%s\n" "$LT_BLUE$BRIGHT" "$VIRTUAL_ENV_FILE_NAME" "$DEFAULT"

