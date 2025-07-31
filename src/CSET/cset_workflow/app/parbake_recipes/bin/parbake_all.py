#! /usr/bin/env python3
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

"""Run a recipe with the CSET CLI."""

import base64
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

from ruamel.yaml import YAML

from CSET._common import parse_recipe, parse_variable_options, slugify

# Load rose suite variables.
ROSE_SUITE_VARIABLES = json.loads(
    base64.b64decode(os.environ["ENCODED_ROSE_SUITE_VARIABLES"], validate=True)
)

# Needed for each diagnostic:
variables: dict[str, str] = {"key": "value"}
model_id: int = 1
recipe_name: str = "generic_surface_spatial_plot_sequence.yaml"
# Then needs to write the new recipe file based on this information.


def parbake(raw_recipe: Path, output_dir: Path, recipe_variables):
    """Parbake a recipe."""
    recipe = parse_recipe(raw_recipe, recipe_variables)
    output = output_dir / f"{slugify(recipe['title'])}.yaml"
    with open(output, "wt") as fp:
        with YAML(pure=True, output=fp) as yaml:
            yaml.dump(recipe)


def get_const_args(environ=os.environ) -> dict:
    """Gather arguments from environment variables that are constant."""
    return {
        "case_aggregation": bool(environ.get("DO_CASE_AGGREGATION")),
        "rose_datac": Path(environ["ROSE_DATAC"]),
        "share_dir": Path(environ["CYLC_WORKFLOW_SHARE_DIR"]),
    }


def get_parbake_args(environ=os.environ) -> dict:
    """Gather per-parbake arguments."""
    return {
        "recipe": Path(environ["CSET_RECIPE_NAME"]),
        "model_identifiers": sorted(environ["MODEL_IDENTIFIERS"].split()),
        "recipe_variables": parse_variable_options(
            shlex.split(environ.get("CSET_ADDOPTS", ""))
        ),
    }


def run_parbake(
    recipe: Path,
    model_identifiers: list[str],
    share_dir: Path,
    rose_datac: Path,
    case_aggregation: bool,
    recipe_variables: dict,
):
    """Pre-process recipe to bake in all variables."""
    print("Retrieving recipe from cookbook.")
    # Ready recipe file to disk.
    subprocess.run(["cset", "-v", "cookbook", str(recipe)], check=True)

    # Collect configuration from environment.
    if case_aggregation:
        # Construct the location for the recipe.
        recipe_dir = rose_datac / "aggregation_recipes"
        # Construct the input data directories for the cycle.
        data_dirs = [
            share_dir / f"cycle/*/data/{model_id}" for model_id in model_identifiers
        ]
    else:
        recipe_dir = rose_datac / "recipes"
        data_dirs = [rose_datac / f"data/{model_id}" for model_id in model_identifiers]

    # Ensure recipe dir exists.
    recipe_dir.mkdir(parents=True, exist_ok=True)

    # Add input paths to recipe variables.
    recipe_variables["INPUT_PATHS"] = str(data_dirs)

    # Parbake recipe.
    print("Parbaking recipe.")
    parbake(raw_recipe=recipe, output_dir=recipe_dir, recipe_variables=recipe_variables)


def run():
    """Run workflow script."""
    try:
        const_args = get_const_args()
        args = get_parbake_args()
        run_parbake(**const_args, **args)
    except subprocess.CalledProcessError:
        sys.exit(1)


if __name__ == "__main__":
    run()
