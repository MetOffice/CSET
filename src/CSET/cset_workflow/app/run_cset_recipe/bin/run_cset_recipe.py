#!/usr/bin/env python3
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

import os
import shlex
import subprocess
import sys


def recipe_file() -> str:
    """Write the recipe file to disk and return its path as a string."""
    # Ready recipe file to disk.
    cset_recipe = os.environ["CSET_RECIPE_NAME"]
    subprocess.run(("cset", "-v", "cookbook", cset_recipe), check=True)
    return cset_recipe


def data_directories() -> list[str]:
    """Get the input data directories for the cycle."""
    model_identifiers = sorted(os.environ["MODEL_IDENTIFIERS"].split())
    if os.getenv("DO_CASE_AGGREGATION"):
        share_dir = os.environ["CYLC_WORKFLOW_SHARE_DIR"]
        return [
            f"{share_dir}/cycle/*/data/{model_id}" for model_id in model_identifiers
        ]
    else:
        rose_datac = os.environ["ROSE_DATAC"]
        return [f"{rose_datac}/data/{model_id}" for model_id in model_identifiers]


def run_recipe_steps():
    """Process data and produce output plots."""
    recipe = recipe_file()
    data_dirs = data_directories()
    # Construct the plot output directory for the recipe.
    output_dir = f"{os.environ['CYLC_WORKFLOW_SHARE_DIR']}/web/plots/{os.environ['CYLC_TASK_ID']}"
    style_file = f"{os.environ['CYLC_WORKFLOW_SHARE_DIR']}/style.json"

    command = (
        ["cset", "bake", "--recipe", recipe, "--input-dir"]
        + data_dirs
        + ["--output-dir", output_dir, "--style-file", style_file]
    )

    plot_resolution = os.getenv("PLOT_RESOLUTION")
    if plot_resolution:
        command.append(f"--plot-resolution={plot_resolution}")

    skip_write = os.getenv("SKIP_WRITE")
    if skip_write:
        command.append("--skip-write")

    print("Running", shlex.join(command))
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as err:
        print(f"cset bake exited with non-zero code {err.returncode}.")
        raise


def run():
    """Run workflow script."""
    try:
        run_recipe_steps()
    except subprocess.CalledProcessError:
        sys.exit(1)


if __name__ == "__main__":
    run()
