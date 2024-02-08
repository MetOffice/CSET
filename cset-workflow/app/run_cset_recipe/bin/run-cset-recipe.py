#! /usr/bin/env python3

"""Run a recipe with the CSET CLI."""

import fcntl
import json
import logging
import os
import subprocess
import zipfile
from pathlib import Path
from uuid import uuid4

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


def append_to_index(index_path: Path, record: dict):
    """Append the plot record to the index file.

    Record should have the form {"Category Name": {"plot_id": "Plot Name"}}
    """
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


# Takes recipe from CSET_RECIPE environment variable if not given.
cset_recipe = os.getenv("CSET_RECIPE_NAME")
if cset_recipe:
    subprocess.run(("cset", "-v", "cookbook", cset_recipe), check=True)
else:
    cset_recipe = Path("recipe.yaml")
    with open(cset_recipe, "wb") as fp:
        fp.write(os.getenvb(b"CSET_RECIPE"))

# TODO: Make plot ID deterministically generated.
# Hashing the recipe here doesn't work as the templating hasn't yet happened.
# with open(cset_recipe, "rb") as fp:
#     plot_id = hashlib.sha256(fp.read()).hexdigest()
plot_id = str(uuid4())

output_directory = Path.cwd() / plot_id
# TODO: I think we might be able to presume the input path.
with open(
    f"{os.getenv('CYLC_WORKFLOW_SHARE_DIR')}/cycle/{os.getenv('CYLC_TASK_CYCLE_POINT')}/input_path",
    "rt",
    encoding="UTF-8",
) as fp:
    input_path = Path(fp.read().strip())

subprocess.run(
    (
        "cset",
        "-v",
        "bake",
        f"--recipe={cset_recipe}",
        f"--input-dir={input_path}",
        f"--output-dir={output_directory}",
    ),
    check=True,
)

# Create archive for easy download of plots and data.
archive_path = output_directory / "diagnostic.zip"
with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in output_directory.rglob("*"):
        # Check the archive doesn't add itself.
        if not path.samefile(archive_path):
            archive.write(path, arcname=path.relative_to(output_directory))

# Get metadata needed for index.
with open(output_directory / "meta.json", "rt", encoding="UTF-8") as fp:
    recipe_meta = json.load(fp)
title = recipe_meta.get("title", "Unknown")
category = recipe_meta.get("category", "Unknown")

# Symbolic link to output from plots directory.
# NOTE: I'm a little dubious, as it means `cylc clean` removes plots.
webdir_path = Path(f"{os.getenv('WEB_DIR')}/plots/{plot_id}")
webdir_path.symlink_to(output_directory, target_is_directory=True)

# Add plot to plot index.
append_to_index(webdir_path.parent / "index.json", {category: {plot_id: title}})
