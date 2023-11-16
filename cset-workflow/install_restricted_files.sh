#! /bin/bash

set -euo pipefail
IFS="$(printf '\n\t')"

echo This script downloads and install Momentum Partnership restricted files and
echo code for use in CSET. To use it make sure you have git cloning via SSH
echo setup for the repository at https://github.com/MetOffice/CSET-workflow

echo "WARNING: This script will overwrite any restricted files."
read -rp 'Continue? [Y/n]: ' choice
if [[ "$choice" == [^Yy]* ]]; then
  echo "Aborted"
  exit 1
fi
unset choice

tempdir="$(mktemp -d)"

# We don't need history, so shallow git clone for speed.
if ! git clone --depth 1 git@github.com:MetOffice/CSET-workflow.git "$tempdir"
then
  echo
  echo Problem cloning git repository.
  echo Check you have SSH cloning set up for https://github.com/MetOffice/CSET-workflow
  exit 1
fi

# Copy most files from there into workflow directory, clobering existing ones.
# Don't copy some files, like README.md or hidden files.
rm "$tempdir"/README.md

# TODO: Swapout rsync for cp. Left as dry-run for testing.
# cp -rv "${tempdir}"/* .
rsync -rv --dry-run "${tempdir}"/* .

# Clean up
rm -rf "$tempdir"
