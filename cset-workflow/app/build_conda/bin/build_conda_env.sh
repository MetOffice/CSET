#! /bin/bash
# This script builds the conda environment used by most subsequent tasks.
set -euo pipefail

# Use default location if CONDA_VENV_LOCATION is not specified.
if [[ -z "$CONDA_VENV_LOCATION" ]]; then
  CONDA_VENV_LOCATION="${CYLC_WORKFLOW_SHARE_DIR}/cset_conda_env"
fi


should_build_conda_env() {
  # Decide if the environment needs building.
  if [[ "$CONDA_VENV_CREATE" == True ]]
  then
    true
  elif [[ "$CONDA_VENV_CREATE" == False ]]
  then
    echo "Conda environment building disabled"
    return 1
  else
    >&2 echo "Invalid value for CONDA_VENV_CREATE: $CONDA_VENV_CREATE"
    exit 1
  fi

  # Find environment definition file, abort if not found.
  env_lock_file="${CYLC_WORKFLOW_RUN_DIR}/requirements/workflow-locks/py313-lock-linux-64.txt"
  if [[ -f "$env_lock_file" ]]
  then
    echo "Using environment file $env_lock_file"
  else
    >&2 echo "Environment file $env_lock_file not found"
    exit 1
  fi

  if [[ -f "${CONDA_VENV_LOCATION}/cset_env_hash" ]]
  then
    if [[ "$(cat "${CONDA_VENV_LOCATION}/cset_env_hash")" == "$(sha256sum "$env_lock_file" | head -c 64)" ]]
    then
      echo "Conda environment already exist, no build required"
      return 1
    else
      echo "Conda environment is out of date, building afresh"
    fi
  else
    echo "Conda environment does not exist, building afresh"
  fi

  return 0
}


build_conda_env() {
  # Source modules/paths required to build the environment.
  if [[ $CSET_ENV_USE_MODULES == True ]]
  then
    if [[ $MODULES_LIST ]]
    then
      if [[ $MODULES_PURGE == True ]]
      then
        module purge
      fi
      for build_module in $MODULES_LIST
      do
        # Loads the same modules that the other tasks uses, although it only needs
        # a module to make conda available. This is to simplify the logic.
        module load "$build_module"
      done
      echo "Sourcing conda via modules:"
      module list
    fi
  fi

  if [[ -d "$CONDA_PATH" ]]
  then
    echo "Sourcing conda from: ${CONDA_PATH}"
  else
    CONDA_PATH=""
  fi

  # Remove old conda environment.
  echo "Removing conda environment with:"
  echo "${CONDA_PATH}conda remove -p $CONDA_VENV_LOCATION --all --yes --quiet"
  if ! "${CONDA_PATH}conda" remove -p "$CONDA_VENV_LOCATION" --all --yes --quiet
  then
    >&2 echo "Failed to conda remove old environment, trying to remove manually."
    rm -rf -- "$CONDA_VENV_LOCATION"
  fi

  # Build conda environment.
  echo "Building conda with:"
  echo "${CONDA_PATH}conda create -p $CONDA_VENV_LOCATION --file $env_lock_file --yes --force --quiet"
  "${CONDA_PATH}conda" create -p "$CONDA_VENV_LOCATION" --file "$env_lock_file" --yes --force --quiet

  # Create hash file for next run.
  sha256sum "$env_lock_file"  | head -c 64 > "${CONDA_VENV_LOCATION}/cset_env_hash"
}


if should_build_conda_env
then
  build_conda_env
fi

# Install development version of CSET into the conda environment if needed, and
# validate CSET is installed. This needs to run inside the conda environment.
app_env_wrapper install-local-cset.sh
