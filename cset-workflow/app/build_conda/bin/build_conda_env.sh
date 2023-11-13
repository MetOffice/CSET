#! /bin/bash
# This script builds the conda environment used by most subsequent tasks.
set -euo pipefail
IFS="$(printf '\n\t')"

# Decide if the environment needs building.
if [[ "$CONDA_VENV_CREATE" == True ]]; then
  true
elif [[ "$CONDA_VENV_CREATE" == False ]]; then
  echo "Conda environment building disabled"
  exit 0
else
  echo "Invalid value for CONDA_VENV_CREATE: $CONDA_VENV_CREATE"
  exit 1
fi

# Find environment definition file, abort if not found.
env_lock_file="$CYLC_WORKFLOW_RUN_DIR/requirements/locks/py311-lock-linux-64.txt"
if [[ -f "$env_lock_file" ]]; then
  echo "Using environment file $env_lock_file"
else
  echo "Environment file $env_lock_file not found"
  exit 1
fi

if [[ -f "$CONDA_VENV_LOCATION/cset_env_hash" ]]; then
  if [[ "$(cat "$CONDA_VENV_LOCATION/cset_env_hash")" == "$(sha256sum "$env_lock_file" | head -c 64)" ]]
  then
    echo "Conda environment already exist, no build required"
    exit 0
  else
    echo "Conda environment is out of date, building afresh"
  fi
else
  echo "Conda environment does not exist, building afresh"
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
    echo "sourcing conda via modules:"
    module list
  fi
fi
if [[ -d "$CONDA_PATH" ]]; then
  echo "Sourcing conda on path: ${CONDA_PATH}"
else
  CONDA_PATH=""
fi

# Remove old conda environment.
rm -rf -- "$CONDA_VENV_LOCATION"

# Build conda environment.
echo "Building conda with:"
echo "${CONDA_PATH}conda create -p $CONDA_VENV_LOCATION --file $env_lock_file --yes --force --quiet"
"${CONDA_PATH}conda" create -p "$CONDA_VENV_LOCATION" --file "$env_lock_file" --yes --force --quiet

# Create hash file for next run.
sha256sum "$env_lock_file"  | head -c 64 > "$CONDA_VENV_LOCATION/cset_env_hash"
