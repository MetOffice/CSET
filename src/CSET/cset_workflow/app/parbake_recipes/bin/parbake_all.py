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

import base64
import json
import os
from pathlib import Path

from CSET.recipes import RawRecipe, spatial_field

# Load rose suite variables.
ROSE_SUITE_VARIABLES = json.loads(
    base64.b64decode(os.environ["ENCODED_ROSE_SUITE_VARIABLES"], validate=True)
)

# Constant directories.
ROSE_DATAC = Path(os.environ["ROSE_DATAC"])
SHARE_DIR = Path(os.environ["CYLC_WORKFLOW_SHARE_DIR"])

# Whether we are doing aggregation recipes.
CASE_AGGREGATION = bool(os.getenv("DO_CASE_AGGREGATION"))


def parbake_all():
    """Generate and parbake recipes from configuration."""
    # Gather all recipes.
    recipes: list[RawRecipe] = []
    recipes += spatial_field.recipes(ROSE_SUITE_VARIABLES).recipes

    # Filter case aggregation recipes.
    recipes = list(filter(lambda r: r.aggregation == CASE_AGGREGATION, recipes))

    # Parbake all remaining recipes.
    for recipe in recipes:
        recipe.parbake(ROSE_DATAC, SHARE_DIR)


if __name__ == "__main__":
    parbake_all()
