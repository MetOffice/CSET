#! /bin/bash

# Install development version of CSET into the conda environment.

set -euo pipefail

cset_install_path="$(mktemp -d)"
cset_source_path="${CSET_LOCAL_CSET_PATH}"
echo "Using local CSET from ${cset_source_path}"

# Directly install wheel files, or copy source folder.
if [[ $cset_source_path == *.whl ]]
then
    echo "Wheel file, installing directly."
    cset_install_path="${cset_source_path}"
else
    # Copy project to temporary location to avoid permissions issues. We
    # don't want to copy all hidden files, as they can contain large conda
    # environments, but we do want the .git directory.
    cp -r "${cset_source_path}"/* "${cset_source_path}"/.git "${cset_install_path}"
fi

# Build and install into conda environment.
pip install --verbose --progress-bar off --no-deps -- "${cset_install_path}"

# Basic test that it installed successfully.
echo "Using CSET version: $(cset --version)"
