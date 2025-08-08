#!/usr/bin/env bash

set -euo pipefail
IFS="$(printf '\n\t')"

show_help()
{
  cat << EOF
Usage: ${0} [-b branch-name] [-R repository]

  * Repository defaults to https://github.com/MetOffice/CSET-workflow
  * Branch defaults to main
  * Most people should omit both, and use the default values

This script downloads and install Momentum® Partnership restricted files and
code for use in CSET. Make sure you have git authentication setup for the
repository at https://github.com/MetOffice/CSET-workflow
EOF
  exit "$1"
}

# Set defaults. These are left unchanged if the option isn't specified.
branch="main"
httpurl="https://github.com/MetOffice/CSET-workflow"

# Parse options.
while getopts "hb:R:" opt
do
  case "$opt" in
    b) branch="$OPTARG"
    ;;
    R) httpurl="$OPTARG"
    ;;
    h) show_help 0
    ;;
    ?) show_help 1
  esac
done

# Basic check that we are in the right folder.
if [[ ! -f flow.cylc ]]
then
  echo "You must be in the cset-workflow directory when running this script."
  exit 1
fi

# Convert GitHub HTTPS url into SSH one.
# GitLab prepends `ssh.` to its SSH URLs, so is not currently supported.
sshurl="$(echo "$httpurl" | sed -e 's/https:\/\//git@/' -e 's/\//:/')"

# Make a temporary directory into which to clone the repository.
tempdir="$(mktemp -d)"

# We don't need history, so shallow git clone for speed.
# First try with SSH cloning.
echo "Cloning ${branch} from ${sshurl}"
if ! git clone --branch "${branch}" --depth 1 "${sshurl}" "${tempdir}"
then
  echo "Cannot clone via SSH, falling back to HTTPS."
  echo "Cloning ${branch} from ${httpurl}"
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
# Clean up. Must force here to remove .git folder.
rm -rf "${tempdir}"

# Report success.
cat << EOF
   ___________ ____________
  / ____/ ___// ____/_  __/
 / /    \__ \/ __/   / /
/ /___ ___/ / /___  / /
\____//____/_____/ /_/

Restricted files installed!
EOF
