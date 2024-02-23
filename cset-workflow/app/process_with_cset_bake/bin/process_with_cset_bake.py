#! /usr/bin/env python3

"""Run a recipe with the CSET CLI."""

import logging
import os
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO)


def get_recipe_id(recipe: Path):
    """Get the ID for the recipe."""
    p = subprocess.run(
        ("cset", "recipe-id", "--recipe", cset_recipe), check=True, capture_output=True
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
data_directory = Path(
    os.getenv("CYLC_WORKFLOW_SHARE_DIR"),
    "cycle",
    os.getenv("CYLC_TASK_CYCLE_POINT"),
    "data",
)
output_directory = Path(os.getenv("CYLC_WORKFLOW_SHARE_DIR"), "plots", recipe_id)

# Run the recipe to process the data and produce any plots.
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
)
