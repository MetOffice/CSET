#! /usr/bin/env python3

"""Run a recipe with the CSET CLI."""

import fcntl
import json
import logging
import os
import subprocess
import zipfile
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


def get_recipe_id(recipe: Path):
    """Get the ID for the recipe."""
    p = subprocess.run(
        ("cset", "recipe-id", "--recipe", recipe), check=True, capture_output=True
    )
    recipe_id = p.stdout.decode("UTF-8").strip()
    return recipe_id


# Ready recipe file to disk.
cset_recipe = Path(os.getenv("CSET_RECIPE_NAME"))
if cset_recipe:
    subprocess.run(("cset", "-v", "cookbook", cset_recipe), check=True)
else:
    # Read recipe YAML from environment variable.
    cset_recipe = Path("recipe.yaml")
    with open(cset_recipe, "wb") as fp:
        fp.write(os.getenvb(b"CSET_RECIPE"))

# Debug check that recipe has been retrieved.
assert cset_recipe.exists()

recipe_id = get_recipe_id(cset_recipe)
cycle_point = os.getenv("CYLC_TASK_CYCLE_POINT")
data_directory = Path(
    os.getenv("CYLC_WORKFLOW_SHARE_DIR"),
    "cycle",
    cycle_point,
    "data",
)
output_directory = Path(os.getenv("CYLC_WORKFLOW_SHARE_DIR"), "plots", recipe_id)
subprocess_environment = {
    # Add validity time based on cycle point.
    "CSET_ADDOPTS": f"{os.getenv("CSET_ADDOPTS")} --VALIDITY_TIME={cycle_point}",
    # Standard environment variables that CSET uses.
    "TMPDIR": os.getenv("TMPDIR"),
}

# If intermediate directory doesn't exists then this is a simple
# non-parallelised recipe, and we need to run cset bake to process the data and
# produce any plots.
if not (output_directory / "intermediate").exists():
    subprocess.run(
        (
            "cset",
            "-v",
            "bake",
            f"--recipe={cset_recipe}",
            f"--input-dir={data_directory}",
            f"--output-dir={output_directory}",
        ),
        check=True,
        env=subprocess_environment,
    )

# Collate intermediate data and produce plots.
subprocess.run(
    (
        "cset",
        "-v",
        "collate",
        f"--recipe={cset_recipe}",
        f"--output-dir={output_directory}",
    ),
    check=True,
    env=subprocess_environment,
)

# Create archive for easy download of plots and data.
archive_path = output_directory / "diagnostic.zip"
with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for file in output_directory.rglob("*"):
        # Check the archive doesn't add itself.
        if not file.samefile(archive_path):
            archive.write(file, arcname=file.relative_to(output_directory))

# Get metadata needed for index.
with open(output_directory / "meta.json", "rt", encoding="UTF-8") as fp:
    recipe_meta = json.load(fp)
title = recipe_meta.get("title", "Unknown")
category = recipe_meta.get("category", "Unknown")

# Add plot to plot index.
append_to_index({category: {recipe_id: title}})
