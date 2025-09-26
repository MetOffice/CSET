# © Crown copyright, Met Office (2022-2025) and CSET contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Useful functions for the workflow."""

import base64
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


def get_models(rose_variables: dict) -> list[dict]:
    """Load per-model configuration into a single object.

    Returns a list of dictionaries, each one containing a per-model
    configuration.
    """
    models = []
    for model in range(1, 20):
        model_prefix = f"m{model}_"
        model_vars = {
            key.removeprefix(model_prefix): value
            for key, value in rose_variables.items()
            if key.startswith(model_prefix)
        }
        if model_vars:
            model_vars["id"] = model
            models.append(model_vars)
    return models


def b64json(d: dict | list) -> str:
    """Encode an object as base64 encoded JSON for transport though cylc."""
    new_d = d.copy()
    if isinstance(new_d, dict):
        # Remove circular reference to ROSE_SUITE_VARIABLES.
        new_d.pop("ROSE_SUITE_VARIABLES", None)
    output = base64.b64encode(json.dumps(new_d).encode()).decode()
    return output


def mix_recipes(rose_variables: dict):
    """Load recipe and task names.

    Loads recipe files and generates unique task names for them.
    """

    def _is_True(val: Any) -> bool:
        if isinstance(val, str):
            return val.lower() in ["true"]
        # use explicit comparison to handle jinja2
        # true/false types
        return val == True  # noqa: E712

    shell_commands = []

    if _is_True(rose_variables.get("CSET_ENV_USE_MODULES", False)):
        shell_commands.append("IFS_SAVE=$IFS; IFS=' '")
        if _is_True(rose_variables.get("MODULES_PURGE", False)):
            shell_commands.append("module purge")
        for module in rose_variables.get("MODULES_LIST", []):
            shell_commands.append(f"module load {module}")
        shell_commands.append("IFS=$IFS_SAVE")

    conda_path = Path(rose_variables.get("CONDA_PATH", ""))

    workflow_dir = Path(os.getcwd())
    linked_conda_environment = workflow_dir / "conda-environment"
    mix_command = (
        f"{workflow_dir / 'app' / 'parbake_recipes' / 'bin' / 'parbake.py'} --premix"
    )
    if linked_conda_environment.exists():
        LOGGER.debug(f"Activating conda environment from {conda_path}")
        shell_commands.append(
            f"{conda_path / 'conda'} run --no-capture-output --prefix {linked_conda_environment} {mix_command}"
        )
    else:
        try:
            subprocess.run(["conda info --envs | grep -q '^cset-dev '"], check=True)
            LOGGER.debug("Activating conda environment from cset-dev")
            shell_commands.append(
                f"{conda_path / 'conda'} run --no-capture-output --name cset-dev {mix_command}"
            )
        except subprocess.CalledProcessError:
            LOGGER.debug(
                "No conda environment to use. Attempting last-ditch attempt to run directly."
            )
            shell_commands.append(mix_command)

    premixing_env = os.environ.copy()
    premixing_env["ENCODED_ROSE_SUITE_VARIABLES"] = b64json(rose_variables)

    p = subprocess.run(
        " && ".join(shell_commands),
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        env=premixing_env,
    )
    results = json.loads(base64.b64decode(p.stdout))

    return results
