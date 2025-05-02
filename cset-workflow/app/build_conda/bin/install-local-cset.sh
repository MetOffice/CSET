#! /bin/bash
set -xv

# Install development version of CSET into the conda environment if needed.

set -euo pipefail

if [[ $CSET_ENV_USE_LOCAL_CSET = "True" ]]; then
  if [[ -e $CSET_LOCAL_CSET_PATH ]]; then
    cset_source_path="${CSET_LOCAL_CSET_PATH}"
    echo "Using local CSET from ${cset_source_path}"
  else
    echo "${CSET_LOCAL_CSET_PATH:-''}" does not exist. Make sure CSET_LOCAL_CSET_PATH is set correctly.
    exit 1
  fi

  # Directly install wheel files or copy, build, and install source folder.
  if [[ $cset_source_path == *.whl ]]; then
    echo "Wheel file, installing directly."
    pip install --progress-bar off --no-deps -- "${cset_source_path}"
  else
    # Copy project to temporary location to avoid permissions issues. We
    # don't want to copy all hidden files, as they can contain large conda
    # environments, but we do want the .git directory.
    cset_install_path="$(mktemp -d)"
    echo "Copying source files to ${cset_install_path}"
    cp -r "${cset_source_path}"/* "${cset_source_path}"/.git "${cset_install_path}"

    # Build and install into conda environment.
    pip install --progress-bar off --no-deps -- "${cset_install_path}"

    # Clean up copied source files.
    rm -rf "${cset_install_path}"
  fi
fi

# Basic test that CSET installed successfully.
echo "Using CSET version: $(cset --version)"
