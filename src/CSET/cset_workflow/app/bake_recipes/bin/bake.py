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

"""Run CSET bake in parallel over recipe files."""

import concurrent.futures
import glob
import os
import shlex
import subprocess
import sys


def get_configuration() -> tuple[list[str], str, list[str], int]:
    """Derive the configuration from the environment.

    Environment Inputs
    ------------------
    Required:
        CYLC_WORKFLOW_SHARE_DIR
        CYLC_TASK_CYCLE_POINT
    Optional:
        COLORBAR_FILE
        PLOT_RESOLUTION
        SKIP_WRITE
        DO_CASE_AGGREGATION

    Returns
    -------
    (cset_args, plot_dir, recipe_files, nproc)
        A tuple of the various configuration items needed.
    """
    share_dir = os.environ["CYLC_WORKFLOW_SHARE_DIR"]
    cycle_point = os.environ["CYLC_TASK_CYCLE_POINT"]

    # Glob recipes files and pick number of concurrent processes depending on
    # whether we are aggregating across case studies.
    if bool(os.getenv("DO_CASE_AGGREGATION")):
        # Run aggregation recipes serially to avoid memory exhaustion.
        nproc = 1
        recipe_files = glob.glob(
            f"{share_dir}/cycle/{cycle_point}/aggregation_recipes/*.yaml"
        )
    else:
        # os.process_cpu_count is python 3.13 or later.
        nproc = len(os.sched_getaffinity(0))
        recipe_files = glob.glob(f"{share_dir}/cycle/{cycle_point}/recipes/*.yaml")

    # Build up an array of arguments.
    cset_args = []
    colorbar_file = os.getenv("COLORBAR_FILE")
    if colorbar_file:
        cset_args.append(f"--style-file='{share_dir}/style.json'")
    plot_resolution = os.getenv("PLOT_RESOLUTION")
    if plot_resolution:
        cset_args.append(f"--plot-resolution={plot_resolution}")
    skip_write = os.getenv("SKIP_WRITE")
    if skip_write:
        cset_args.append("--skip-write")

    # Put together path to plot dir.
    plot_dir = f"{share_dir}/web/plots/{cycle_point}"

    return cset_args, plot_dir, recipe_files, nproc


def bake_recipe(recipe_file: str, cset_args: list[str], plot_dir: str) -> str:
    """Bake a single recipe."""
    recipe_name = recipe_file.split("/")[-1].removesuffix(".yaml")
    output_dir = f"{plot_dir}/{recipe_name}"
    command = ["cset", "bake", "--recipe", recipe_file, "--output-dir", output_dir]
    command += cset_args
    print("Running", shlex.join(command), file=sys.stderr)
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as err:
        print(f"Baking of {recipe_file} failed. Exited with code {err.returncode}")
        raise
    return recipe_name


def bake_all():
    """Bake all of the recipes for this configuration."""
    cset_args, plot_dir, recipe_files, nproc = get_configuration()

    def bake(recipe_file: str) -> str:
        """Partial function for submitting to the executor."""
        return bake_recipe(recipe_file, cset_args, plot_dir)

    # Run concurrent baking jobs.
    with concurrent.futures.ThreadPoolExecutor(max_workers=nproc) as executor:
        futures = [executor.submit(bake, rf) for rf in recipe_files]

        total_jobs = len(futures)
        if total_jobs == 0:
            print("No recipes found.")
            sys.exit(1)

        completed_jobs = 0
        padding = len(str(total_jobs))
        print(f"Baking {total_jobs} recipes across {nproc} concurrent jobs...")
        for future in concurrent.futures.as_completed(futures):
            completed_jobs += 1
            print(
                f"{completed_jobs:{padding}}/{total_jobs} Baked {future.result()}",
                flush=True,
            )


def run():
    """Run workflow script."""
    try:
        bake_all()
    except subprocess.CalledProcessError:
        sys.exit(1)


if __name__ == "__main__":
    run()
