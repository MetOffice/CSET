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

import json
import os
from base64 import b64decode
from pathlib import Path

from CSET.recipes import load_recipes


def parbake_all(variables: dict, rose_datac: Path, share_dir: Path, aggregation: bool):
    """Generate and parbake recipes from configuration."""
    # Gather all recipes into a big list.
    recipes = list(load_recipes(variables))
    # Check we have some recipes enabled.
    if not recipes:
        raise ValueError("At least one recipe should be enabled.")
    # Parbake all recipes remaining after filtering aggregation recipes.
    for recipe in filter(lambda r: r.aggregation == aggregation, recipes):
        print(f"Parbaking {recipe}")
        recipe.parbake(rose_datac, share_dir)


def main():
    """Program entry point."""
    # Gather configuration from environment.
    variables = json.loads(b64decode(os.environ["ENCODED_ROSE_SUITE_VARIABLES"]))
    rose_datac = Path(os.environ["ROSE_DATAC"])
    share_dir = Path(os.environ["CYLC_WORKFLOW_SHARE_DIR"])
    aggregation = bool(os.getenv("DO_CASE_AGGREGATION"))
    # Parbake recipes for cycle.
    parbake_all(variables, rose_datac, share_dir, aggregation)


if __name__ == "__main__":  # pragma: no cover
    main()
