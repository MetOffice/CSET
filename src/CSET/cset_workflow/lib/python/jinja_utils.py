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

"""Useful functions for the workflow."""

import base64
import json


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


def b64json(d: dict | list) -> str:
    """Encode an object as base64 encoded JSON for transport though cylc."""
    new_d = d.copy()
    if isinstance(new_d, dict):
        # Remove circular reference to ROSE_SUITE_VARIABLES.
        new_d.pop("ROSE_SUITE_VARIABLES", None)
    output = base64.b64encode(json.dumps(new_d).encode()).decode()
    return output
