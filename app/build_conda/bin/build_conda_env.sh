#! /bin/bash
# This script builds the conda environment used by most subsequent tasks.
set -euxo pipefail

# Find environment definition file, abort if not found.
env_lock_file="${CYLC_WORKFLOW_RUN_DIR}/requirements/development-locks/py313-lock-linux-64.txt"
if [[ -f "$env_lock_file" ]]
then
  echo "Using environment file $env_lock_file"
else
  >&2 echo "Environment file $env_lock_file not found"
  exit 1
fi

# Conda environment name is based on hash of lock file.
conda_env_name="cset-workflow-$(sha256sum "$env_lock_file" | head -c 12)"


should_build_conda_env() {
  # Decide if the environment needs building.
  if [[ "$CONDA_VENV_CREATE" == False ]]
  then
    echo "Conda environment building disabled"
    return 1
  fi

  # Skip building if environment already exists. As we use a hash of the lock
  # files we can just check for the name.
  if conda info --envs | grep "$conda_env_name"
  then
    echo "Conda environment already exist, no build required"
    return 1
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

  # Build conda environment.
  echo "Building conda with:"
  echo "${CONDA_PATH}conda create -n $conda_env_name --file $env_lock_file --yes --force --quiet"
  conda_create_start=$(date +%s)
  "${CONDA_PATH}conda" create -n "$conda_env_name" --file "$env_lock_file" --yes --force --quiet
  conda_create_duration=$(($(date +%s) - conda_create_start))
  echo "Creating conda environment took ${conda_create_duration} seconds"
}


if should_build_conda_env
then
  build_conda_env
fi

# Provide a known path to activate the conda environment.
# BUG: Won't handle conda prefixes containing spaces.
env_prefix="$(conda info --envs | grep -Eo '/[^ ]+'"${conda_env_name}"'$')"
ln -vfs "${env_prefix}" "${CYLC_WORKFLOW_SHARE_DIR}/cset-conda-environment"

# Install CSET into the conda environment and validate CSET is installed.
# This needs to run inside the conda environment.
app_env_wrapper install-local-cset.sh
