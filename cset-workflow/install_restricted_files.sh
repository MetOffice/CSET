#! /bin/bash

set -euo pipefail
IFS="$(printf '\n\t')"

echo "This script downloads and install Momentum Partnership restricted files and"
echo "code for use in CSET. To use it make sure you have git cloning via SSH"
echo "setup for the repository at https://github.com/MetOffice/CSET-workflow"

read -rp 'Remote branch to use? [main]: ' branch
if [[ -z "$branch" ]]
then
  branch="main"
fi

read -rp 'Restricted files will be overwritten. Continue? [Y/n]: ' choice
if [[ "$choice" == [^Yy]* ]]
then
  echo "Aborted"
  exit 1
fi
unset choice

tempdir="$(mktemp -d)"

# We don't need history, so shallow git clone for speed.
if ! git clone --branch "${branch}" --depth 1 git@github.com:MetOffice/CSET-workflow.git "${tempdir}"
then
  echo
  echo "Problem cloning git repository."
  echo "Check you have SSH cloning set up for https://github.com/MetOffice/CSET-workflow"
  exit 1
fi

# Copy most files from there into workflow directory, clobering existing ones.
# Don't copy some files, like README.md or top-level hidden files.
rm "${tempdir}/README.md"

if [[ -z "${1-}" ]]
then
  target_directory="$PWD"
else
  target_directory="$1"
fi

cp -rv "${tempdir}"/* "${target_directory}"

# Clean up, must force here to remove .git folder.
rm -rf "${tempdir}"
