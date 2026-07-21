#!/usr/bin/env bash
# Update conda lock files and pre-commit hooks.
set -euo pipefail

# Create a temporary virtual environment.
venv_location="$(mktemp -d)"
echo "Creating temporary virtual environment at ${venv_location}"
python3 -m venv "${venv_location}"
# shellcheck disable=SC1091
source "${venv_location}/bin/activate"

echo "Installing update tools"
pip install --quiet conda-lock pre-commit

# Create lock files for supported python versions.
py_vers="3.12 3.13 3.14"
env_tmp="$(mktemp -d)"
for py_ver in ${py_vers}
do
    # Developer lock files.
    echo "Updating lock files for python ${py_ver}"
    cp "requirements/environment.yml" "${env_tmp}/${py_ver}_dev_environment.yml"
    echo -e "\n  - python = $py_ver" >> "${env_tmp}/${py_ver}_dev_environment.yml"
    conda-lock --channel conda-forge --kind explicit --file "${env_tmp}/${py_ver}_dev_environment.yml" --platform linux-64 --filename-template "requirements/locks/py${py_ver//.}-lock-linux-64.txt"
done

# Replace Met Office specific URLs with normal ones.
sed -i "s|metoffice.jfrog.io/metoffice/api/conda|conda.anaconda.org|" requirements/locks/*.txt

# Sort lock files to make diffs easier to review.
for file in requirements/locks/*.txt
do
    # Leave the file header unsorted.
    cat "${file}" | (sed -u 4q; sort) > sorted.txt
    mv sorted.txt "${file}"
done

# Record the environment.yml used to build the environment.
sha256sum requirements/environment.yml > requirements/locks/sources

echo "Updating pre-commit hooks"
pre-commit autoupdate --freeze

echo "Cleaning up temporary files"
# Clean up temporary environment definitions.
rm -r "${env_tmp}"
# Clean up virtual environment.
deactivate
rm -r "${venv_location}"
