#! /bin/bash

set -euo pipefail
IFS="$(printf '\n\t')"

if [[ "${1-}" == -h ]] || [[ "${1-}" == --help ]]
then
  cat << EOF
Usage: ${0} [<branch-name>] [<repository-url>]

  * If <repository-url> is omitted it defaults to
    https://github.com/MetOffice/CSET-workflow
  * If <branch-name> is omitted it defaults to main. It cannot be omitted
    if you specify <repository-url>, as they are positional arguments.
  * Most people should omit both, and use the default values.

This script downloads and install Momentum® Partnership restricted files and
code for use in CSET. Make sure you have git authentication setup for the
repository at https://github.com/MetOffice/CSET-workflow
EOF
  exit 0
fi

# Basic check the we are in the right folder.
if [[ ! -f flow.cylc ]]
then
  echo "You must be in the cset-workflow directory when running this script."
  exit 1
fi

if [[ -z "${1-}" ]]
then
  branch="main"
fi

if [[ -z "${2-}" ]]
then
  httpurl="https://github.com/MetOffice/CSET-workflow"
fi
sshurl="$(echo "$httpurl" | sed -e 's/https:\/\//git@/' -e 's/\//:/')"

# Make a temporary directory into which to clone the repository.
tempdir="$(mktemp -d)"

# We don't need history, so shallow git clone for speed.
# First try with SSH cloning.
if ! git clone --branch "${branch}" --depth 1 "${sshurl}" "${tempdir}"
then
  echo "Cannot clone via SSH, falling back to HTTPS."
  if ! git clone --branch "${branch}" --depth 1 "${httpurl}" "${tempdir}"
  then
    echo "Problem cloning git repository."
    echo "Check you have set up access for ${httpurl}"
    exit 1
  fi
fi

# Copy most files from there into workflow directory, clobering existing ones.
# Don't copy some files, like README.md or top-level hidden files.
rm "${tempdir}/README.md"
# Ignores top level hidden files.
cp -rv "${tempdir}"/* "$PWD"

# Clean up, must force here to remove .git folder.
rm -rf "${tempdir}"

echo "Restricted files installed!"
