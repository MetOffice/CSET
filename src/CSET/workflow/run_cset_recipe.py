#! /usr/bin/env python3

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
        if skip_write == "True":
            command.append("--skip-write")

    print("Running", shlex.join(command))
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as err:
        print(f"cset bake exited with non-zero code {err.returncode}.", sys.stderr)
        raise


def run():
    """Run workflow script."""
    try:
        run_recipe_steps()
    except subprocess.CalledProcessError:
        sys.exit(1)
