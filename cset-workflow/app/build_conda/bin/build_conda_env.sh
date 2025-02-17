#! /bin/bash

# Build the conda environment used by most subsequent tasks.

set -euo pipefail

# Find environment definition file, abort if not found.
env_lock_file="${CYLC_WORKFLOW_RUN_DIR}/requirements/workflow-locks/py313-lock-linux-64.txt"
if [[ -f "$env_lock_file" ]]; then
  echo "Using environment file $env_lock_file"
else
  >&2 echo "Environment file $env_lock_file not found"
  exit 1
fi

# Source modules/paths required to build the environment.
if [[ $CSET_ENV_USE_MODULES == True ]]; then
  if [[ $MODULES_LIST ]]; then
    if [[ $MODULES_PURGE == True ]]; then
      module purge
    fi
    for build_module in $MODULES_LIST; do
      # Loads the same modules that the other tasks uses, although it only needs
      # a module to make conda available. This is to simplify the logic.
      module load "$build_module"
    done
    echo "Sourcing conda via modules:"
    module list
  fi
fi

# Build conda environment.
echo "Building conda with:"
echo "${CONDA_PATH:=}conda create -p ${CYLC_WORKFLOW_SHARE_DIR}/cset-conda-environment --file $env_lock_file --yes --force --quiet"
"${CONDA_PATH}conda" create -p "${CYLC_WORKFLOW_SHARE_DIR}/cset-conda-environment" --file "$env_lock_file" --yes --force --quiet

# Install local version of CSET into the conda environment if needed, and
# validate CSET is installed. This needs to run inside the conda environment.
app_env_wrapper install-local-cset.sh
