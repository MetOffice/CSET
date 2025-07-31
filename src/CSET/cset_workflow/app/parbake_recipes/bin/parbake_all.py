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
import subprocess
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from CSET._common import parse_recipe, slugify

# Load rose suite variables.
ROSE_SUITE_VARIABLES = json.loads(
    base64.b64decode(os.environ["ENCODED_ROSE_SUITE_VARIABLES"], validate=True)
)

# Constant directories.
ROSE_DATAC = Path(os.environ["ROSE_DATAC"])
SHARE_DIR = Path(os.environ["CYLC_WORKFLOW_SHARE_DIR"])

# Whether we are doing aggregation recipes.
CASE_AGGREGATION = bool(os.getenv("DO_CASE_AGGREGATION"))


class RawRecipe:
    """A recipe to be parbaked."""

    recipe: str
    model_ids: list[str]
    variables: dict[str, str]
    aggregation: bool

    def __init__(
        self,
        recipe: str,
        model_ids: list[str],
        variables: dict[str, Any],
        aggregation: bool,
    ) -> None:
        # Whether we have an aggregation recipe.
        self.recipe = recipe
        self.model_ids = model_ids
        self.variables = variables
        self.aggregation = aggregation

    def parbake(self) -> None:
        """Pre-process recipe to bake in all variables."""
        print("Retrieving recipe from cookbook.")
        # Ready recipe file to disk.
        subprocess.run(["cset", "-v", "cookbook", self.recipe], check=True)

        # Collect configuration from environment.
        if self.aggregation:
            # Construct the location for the recipe.
            recipe_dir = ROSE_DATAC / "aggregation_recipes"
            # Construct the input data directories for the cycle.
            data_dirs = [
                SHARE_DIR / f"cycle/*/data/{model_id}" for model_id in self.model_ids
            ]
        else:
            recipe_dir = ROSE_DATAC / "recipes"
            data_dirs = [ROSE_DATAC / f"data/{model_id}" for model_id in self.model_ids]

        # Ensure recipe dir exists.
        recipe_dir.mkdir(parents=True, exist_ok=True)

        # Add input paths to recipe variables.
        self.variables["INPUT_PATHS"] = str(data_dirs)

        # Parbake this recipe, saving into recipe_dir.
        print("Parbaking recipe.")
        recipe = parse_recipe(Path(self.recipe), self.variables)
        output = recipe_dir / f"{slugify(recipe['title'])}.yaml"
        with open(output, "wt") as fp:
            with YAML(pure=True, output=fp) as yaml:
                yaml.dump(recipe)


class RecipeList:
    """Collection of RawRecipes with easy adder function."""

    recipes: list[RawRecipe] = []

    def add(self, recipe, model_ids, variables, aggregation):
        """Create a new RawRecipe and add it to the RecipeList."""
        self.recipes.append(
            RawRecipe(
                recipe=recipe,
                model_ids=model_ids,
                variables=variables,
                aggregation=aggregation,
            )
        )


# Utility functions. Probably want to move into own file.
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


def parbake_all():
    """Generate and parbake recipes from configuration."""
    from . import spatial_field

    # Gather all recipes.
    recipes: list[RawRecipe] = []
    recipes += spatial_field.recipes(ROSE_SUITE_VARIABLES).recipes

    # Filter case aggregation recipes.
    recipes = list(filter(lambda r: r.aggregation == CASE_AGGREGATION, recipes))

    # Parbake all remaining recipes.
    for recipe in recipes:
        recipe.parbake()


if __name__ == "__main__":
    parbake_all()
