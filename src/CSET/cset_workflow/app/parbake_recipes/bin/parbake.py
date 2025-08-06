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

import importlib
import json
import os
import pkgutil
from base64 import b64decode
from pathlib import Path

import CSET.recipes


def parbake_all():
    """Generate and parbake recipes from configuration."""
    # Load rose suite variables.
    rose_suite_variables = json.loads(
        b64decode(os.environ["ENCODED_ROSE_SUITE_VARIABLES"])
    )
    # Gather all recipes into a big list.
    recipes = []
    # Try to load recipes from all python modules in CSET.recipes.
    # Implementation based on plugin architecture described at
    # https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/#using-namespace-packages
    loaders = pkgutil.iter_modules(CSET.recipes.__path__, CSET.recipes.__name__ + ".")
    for loader in loaders:
        print(f"Loading recipes from {loader.name}")
        pkg = importlib.import_module(loader.name)
        try:
            recipes.extend(pkg.load(rose_suite_variables))
        except AttributeError as err:
            raise AttributeError(
                f"{loader.name} should provide a `load` function."
            ) from err

    if not recipes:
        raise ValueError("At least one recipe should be enabled.")

    # Whether we are doing aggregation recipes.
    case_aggregation = bool(os.getenv("DO_CASE_AGGREGATION"))

    def aggregation_enabled(recipe) -> bool:
        """Filter to just aggregation or non-aggregation recipes."""
        return recipe.aggregation == case_aggregation

    # Constant directories.
    rose_datac = Path(os.environ["ROSE_DATAC"])
    share_dir = Path(os.environ["CYLC_WORKFLOW_SHARE_DIR"])

    # Parbake all recipes remaining after filtering aggregation recipes.
    for recipe in filter(aggregation_enabled, recipes):
        print(f"Parbaking {recipe}")
        recipe.parbake(rose_datac, share_dir)


if __name__ == "__main__":
    parbake_all()
