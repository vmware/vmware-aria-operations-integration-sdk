#!/bin/sh

#
# Copyright 2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#

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

test_dependency() {
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

if [ "$1" = "--verbose" ] ; then
  VERBOSE=1
else
  VERBOSE=0
fi

printf "%s* Checking Dependencies%s\n" "$MAGENTA" "$DEFAULT"
# Git is almost certainly installed if the user has gotten this far, but we'll test just in case they downloaded an
# archive instead of cloning the repo
test_dependency "Git" "git" "git version 2.35.0" "https://git-scm.com/downloads"
test_dependency "Python" "python3" "Python 3.9.0" "https://wiki.python.org/moin/BeginnersGuide/Download"
test_dependency "Docker" "docker" "Docker version 20.10.0" "https://docs.docker.com/engine/install/"

if [ $DEPENDENCIES_MET = 0 ] ; then
  printf "%sPlease fix above dependency issues and rerun this install script%s\n" "$RED" "$DEFAULT"
  exit 1
fi

printf "%s* Creating Virtual Environment%s\n" "$MAGENTA" "$DEFAULT"
# Add path to repo
STATUS=0
VROPS_SDK_REPO_PATH="$(realpath .)"
STATUS=$((STATUS + $?))
export VROPS_SDK_REPO_PATH
STATUS=$((STATUS + $?))

# Create virtual environment
(python3 -m venv $VIRTUAL_ENV_FILE_NAME)
STATUS=$((STATUS + $?))

# Activate virtual environment to source
source $VIRTUAL_ENV_FILE_NAME/bin/activate
STATUS=$((STATUS + $?))
if [ $STATUS -ne 0 ] ; then
  printf "\n"
  printf "%sError creating or activating the Virtual Environment%s\n" "$RED" "$DEFAULT"
  exit 2
fi

printf "%s* Installing SDK tools into Virtual Environment%s\n" "$MAGENTA" "$DEFAULT"
  STATUS=0
## Install our package
if [ $VERBOSE = 1 ] ; then
  pip install .
  STATUS=$((STATUS + $?))
  # TODO: Remove this once we are on the official PyPi server
  pip install -i https://test.pypi.org/simple/ vmware-aria-operations-integration-sdk-lib
  STATUS=$((STATUS + $?))
else
  pip install . > /dev/null
  STATUS=$((STATUS + $?))
  # TODO: Remove this once we are on the official PyPi server
  pip install -i https://test.pypi.org/simple/ vmware-aria-operations-integration-sdk-lib > /dev/null
  STATUS=$((STATUS + $?))
fi

if [ $STATUS -ne 0 ] ; then
  printf "\n"
  printf "%sError installing SDK tools or dependencies into Virtual Environment%s\n" "$RED" "$DEFAULT"
  exit 3
fi


printf "%sInstallation completed. Run the following command to activate the virtual environment:%s\n" "$GREEN" "$DEFAULT"
printf "%ssource %s/bin/activate%s\n" "$LT_BLUE$BRIGHT" "$VIRTUAL_ENV_FILE_NAME" "$DEFAULT"

