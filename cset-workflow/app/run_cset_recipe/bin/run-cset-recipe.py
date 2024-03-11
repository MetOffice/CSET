#! /usr/bin/env python3

"""Run a recipe with the CSET CLI."""

import fcntl
import json
import logging
import os
import subprocess
import sys
import zipfile
from functools import cache
from pathlib import Path

logging.basicConfig(level=logging.INFO)


def combine_dicts(d1: dict, d2: dict) -> dict:
    """Recursively combines two dictionaries.

    Duplicate atoms favour the second dictionary.
    """
    # Update existing keys.
    for key in d1.keys() & d2.keys():
        if isinstance(d1[key], dict):
            d1[key] = combine_dicts(d1[key], d2[key])
        else:
            d1[key] = d2[key]
    # Add any new keys.
    for key in d2.keys() - d1.keys():
        d1[key] = d2[key]
    return d1


def append_to_index(record: dict):
    """Append the plot record to the index file.

    Record should have the form {"Category Name": {"recipe_id": "Plot Name"}}
    """
    # Plot index is at {run}/share/plots/index.json
    index_path = Path(os.getenv("CYLC_WORKFLOW_SHARE_DIR"), "plots/index.json")
    with open(index_path, "a+t", encoding="UTF-8") as fp:
        # Lock file until closed.
        fcntl.flock(fp, fcntl.LOCK_EX)
        # Open in append mode then seek back to avoid errors if the file does
        # not exist.
        fp.seek(0)
        try:
            index = json.load(fp)
        except json.JSONDecodeError:
            index = {}
        index = combine_dicts(index, record)
        fp.seek(0)
        fp.truncate()
        json.dump(index, fp)


@cache
def subprocess_env():
    """Create a dictionary of amended environment variables for subprocess."""
    env_mapping = dict(os.environ)
    cycle_point = env_mapping["CYLC_TASK_CYCLE_POINT"]
    # Add validity time based on cycle point.
    env_mapping[
        "CSET_ADDOPTS"
    ] = f"{os.getenv("CSET_ADDOPTS", '')} --VALIDITY_TIME={cycle_point}"
    return env_mapping


@cache
def recipe_file():
    """Write the recipe file to disk and return its path."""
    # Ready recipe file to disk.
    cset_recipe = os.getenv("CSET_RECIPE_NAME")
    if cset_recipe:
        subprocess.run(("cset", "-v", "cookbook", cset_recipe), check=True)
    else:
        # Read recipe YAML from environment variable.
        cset_recipe = "recipe.yaml"
        with open(cset_recipe, "wb") as fp:
            fp.write(os.getenvb(b"CSET_RECIPE"))

    # Debug check that recipe has been retrieved.
    assert Path(cset_recipe).is_file()

    return cset_recipe


@cache
def recipe_id():
    """Get the ID for the recipe."""
    p = subprocess.run(
        ("cset", "recipe-id", "--recipe", recipe_file()),
        check=True,
        capture_output=True,
        env=subprocess_env(),
    )
    id = p.stdout.decode("UTF-8").strip()
    return id


def output_directory():
    """Get the plot output directory for the recipe."""
    share_directory = os.environ["CYLC_WORKFLOW_SHARE_DIR"]
    return f"{share_directory}/plots/{recipe_id()}"


def data_directory():
    """Get the input data directory for the cycle."""
    share_directory = os.environ["CYLC_WORKFLOW_SHARE_DIR"]
    cycle_point = os.environ["CYLC_TASK_CYCLE_POINT"]
    return f"{share_directory}/cycle/{cycle_point}/data"


def create_diagnostic_archive(output_directory):
    """Create archive for easy download of plots and data."""
    output_directory = Path(output_directory)
    archive_path = output_directory / "diagnostic.zip"
    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        for file in output_directory.rglob("*"):
            # Check the archive doesn't add itself.
            if not file.samefile(archive_path):
                archive.write(file, arcname=file.relative_to(output_directory))


def add_to_diagnostic_index(output_directory, recipe_id):
    """Add the diagnostic to the plot index if it isn't already there."""
    output_directory = Path(output_directory)
    with open(output_directory / "meta.json", "rt", encoding="UTF-8") as fp:
        recipe_meta = json.load(fp)
    title = recipe_meta.get("title", "Unknown")
    category = recipe_meta.get("category", "Unknown")

    # Add plot to plot index.
    append_to_index({category: {recipe_id: title}})


def collate():
    """Collate processed data together and produce output plot."""
    # If intermediate directory doesn't exists then we are running a simple
    # non-parallelised recipe, and we need to run cset bake to process the data
    # and produce any plots. So we actually get some usage out of it, we are
    # using the non-restricted form of bake, so it runs both the processing and
    # collation steps.
    try:
        if not Path(output_directory(), "intermediate").exists():
            subprocess.run(
                (
                    "cset",
                    "-v",
                    "bake",
                    f"--recipe={recipe_file()}",
                    f"--input-dir={data_directory()}",
                    f"--output-dir={output_directory()}",
                ),
                check=True,
                env=subprocess_env(),
            )
        else:
            # Collate intermediate data and produce plots.
            subprocess.run(
                (
                    "cset",
                    "-v",
                    "bake",
                    f"--recipe={recipe_file()}",
                    f"--output-dir={output_directory()}",
                    "--post-only",
                ),
                check=True,
                env=subprocess_env(),
            )
    except subprocess.CalledProcessError:
        logging.error("cset bake exited non-zero while collating.")
        sys.exit(1)
    create_diagnostic_archive(output_directory())
    add_to_diagnostic_index(output_directory(), recipe_id())


def process():
    """Process raw data."""
    try:
        subprocess.run(
            (
                "cset",
                "-v",
                "bake",
                f"--recipe={recipe_file()}",
                f"--input-dir={data_directory()}",
                f"--output-dir={output_directory()}",
                "--pre-only",
            ),
            check=True,
            env=subprocess_env(),
        )
    except subprocess.CalledProcessError:
        logging.error("cset bake exited non-zero while processing.")
        sys.exit(1)


if __name__ == "__main__":
    # Check if we are running in process or collate mode.
    bake_mode = os.getenv("CSET_BAKE_MODE")
    if bake_mode == "process":
        process()
    elif bake_mode == "collate":
        collate()
