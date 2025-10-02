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
import subprocess
from base64 import b64decode
from pathlib import Path

from CSET.recipes import load_recipes


def parbake_all(
    variables: dict, rose_datac: Path, share_dir: Path, aggregation: bool
) -> int:
    """Generate and parbake recipes from configuration."""
    # Gather all recipes into a big list.
    recipes = list(load_recipes(variables))
    # Check we have some recipes enabled.
    if not recipes:
        raise ValueError("At least one recipe should be enabled.")
    # Parbake all recipes remaining after filtering aggregation recipes.
    recipe_count = 0
    for recipe in filter(lambda r: r.aggregation == aggregation, recipes):
        print(f"Parbaking {recipe}", flush=True)
        recipe.parbake(rose_datac, share_dir)
        recipe_count += 1
    return recipe_count


def main():
    """Program entry point."""
    # Gather configuration from environment.
    variables = json.loads(b64decode(os.environ["ENCODED_ROSE_SUITE_VARIABLES"]))
    rose_datac = Path(os.environ["ROSE_DATAC"])
    share_dir = Path(os.environ["CYLC_WORKFLOW_SHARE_DIR"])
    aggregation = bool(os.getenv("DO_CASE_AGGREGATION"))
    # Parbake recipes for cycle.
    recipe_count = parbake_all(variables, rose_datac, share_dir, aggregation)

    # If running under cylc, notify cylc of task completion.
    cylc_workflow_id = os.environ.get("CYLC_WORKFLOW_ID", None)
    cylc_task_job = os.environ.get("CYLC_TASK_JOB", None)
    if cylc_workflow_id and cylc_task_job:
        message_command = [
            "cylc",
            "message",
            "--",
            cylc_workflow_id,
            cylc_task_job,
        ]
        if recipe_count > 0:
            subprocess.run(message_command + ["start baking"])
        else:
            subprocess.run(message_command + ["skip baking"])


if __name__ == "__main__":  # pragma: no cover
    main()
