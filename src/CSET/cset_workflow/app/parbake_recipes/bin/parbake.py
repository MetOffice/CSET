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
import warnings
from base64 import b64decode
from pathlib import Path

import CSET.recipes

# Load rose suite variables.
ROSE_SUITE_VARIABLES = json.loads(b64decode(os.environ["ENCODED_ROSE_SUITE_VARIABLES"]))

# Constant directories.
ROSE_DATAC = Path(os.environ["ROSE_DATAC"])
SHARE_DIR = Path(os.environ["CYLC_WORKFLOW_SHARE_DIR"])

# Whether we are doing aggregation recipes.
CASE_AGGREGATION = bool(os.getenv("DO_CASE_AGGREGATION"))


def aggregation_enabled(recipe) -> bool:
    """Filter to just aggregation or non-aggregation recipes."""
    return recipe.aggregation == CASE_AGGREGATION


def parbake_all():
    """Generate and parbake recipes from configuration."""
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
            recipes.extend(pkg.load(ROSE_SUITE_VARIABLES))
        except AttributeError:
            warnings.warn(
                f"{loader.name} did not have a 'load' function.", stacklevel=2
            )

    # Parbake all recipes remaining after filtering aggregation recipes.
    for recipe in filter(aggregation_enabled, recipes):
        print(f"Parbaking {recipe}")
        recipe.parbake(ROSE_DATAC, SHARE_DIR)


if __name__ == "__main__":
    parbake_all()
